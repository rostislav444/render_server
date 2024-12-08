import os
import asyncio
import aiohttp
from typing import List, Dict
import logging
from dataclasses import dataclass

from render_object_parts import print_to_console
from settings import domain, media_path, filter_parts, ids

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class UploadTask:
    material_id: int
    file_path: str
    variant_pk: int
    blender_name: str
    model_n: int
    camera_n: int
    total_cameras: int
    material_n: int
    total_materials: int


async def send_image_async(session: aiohttp.ClientSession, task: UploadTask) -> bool:
    """Асинхронная отправка одного изображения"""
    url = f"{domain}/api/product/load_scene_material/"

    try:
        # Формируем данные для отправки
        data = aiohttp.FormData()
        data.add_field('scene_material', str(task.material_id))
        data.add_field('image',
                       open(task.file_path, 'rb'),
                       filename=os.path.basename(task.file_path))

        async with session.post(url, data=data) as response:
            if response.status == 200:
                logger.info(f"Successfully uploaded {task.file_path}")
                return True
            else:
                logger.error(f"Failed to upload {task.file_path}: {response.status}")
                return False

    except Exception as e:
        logger.error(f"Error uploading {task.file_path}: {str(e)}")
        return False


async def process_upload_tasks(tasks: List[UploadTask], semaphore: asyncio.Semaphore):
    """Обработка всех задач загрузки с ограничением одновременных запросов"""
    async with aiohttp.ClientSession() as session:
        # Создаем список корутин с семафором
        async def bounded_upload(task):
            async with semaphore:
                print_to_console(False, task.variant_pk, task.blender_name,
                                 task.model_n, task.camera_n, task.total_cameras,
                                 task.material_n, task.total_materials)
                return await send_image_async(session, task)

        # Запускаем все задачи и ждем их завершения
        results = await asyncio.gather(
            *(bounded_upload(task) for task in tasks),
            return_exceptions=True
        )
        return results


async def process_model_3d(data: Dict, pk: int) -> List[UploadTask]:
    """Обработка модели и создание списка задач для загрузки"""
    tasks = []

    for model_n, model_3d in enumerate(data['model_3d'], 1):
        for camera_n, camera in enumerate(model_3d['cameras'], 1):
            for part in camera['parts']:
                blender_name = part['part']['blender_name']

                if len(filter_parts) == 0 or blender_name in filter_parts:
                    dir_name = os.path.join('variant_%d' % pk,
                                            'model_%d' % model_n,
                                            'camera_%d' % camera_n,
                                            blender_name)

                    materials_count = len(part['materials'])
                    for material_n, material in enumerate(part['materials'], 1):
                        material_id = material['material']
                        filepath = dir_name + '/' + material_id + '.png'
                        media_filepath = os.path.join(media_path, filepath)

                        if os.path.exists(media_filepath) and material['image'] is None:
                            task = UploadTask(
                                material_id=material['id'],
                                file_path=media_filepath,
                                variant_pk=pk,
                                blender_name=blender_name,
                                model_n=model_n,
                                camera_n=camera_n,
                                total_cameras=len(model_3d['cameras']),
                                material_n=material_n,
                                total_materials=materials_count
                            )
                            tasks.append(task)

    return tasks


async def main():
    # Создаем семафор для ограничения количества одновременных запросов
    semaphore = asyncio.Semaphore(10)

    for product_id in ids:
        try:
            # Получаем данные о продукте
            async with aiohttp.ClientSession() as session:
                url = f'{domain}/api/product/render/{product_id}/'
                async with session.get(url) as response:
                    if response.status != 200:
                        logger.error(f'Failed to get product data: {response.status}')
                        continue
                    data = await response.json()

            # Создаем список задач для загрузки
            upload_tasks = await process_model_3d(data, product_id)

            # Запускаем загрузку всех файлов
            results = await process_upload_tasks(upload_tasks, semaphore)

            # Анализируем результаты
            success_count = sum(1 for r in results if r is True)
            logger.info(f"Completed product {product_id}. "
                        f"Successfully uploaded {success_count} of {len(results)} files.")

        except Exception as e:
            logger.error(f"Error processing product {product_id}: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())