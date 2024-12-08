import os
import asyncio
import aiohttp
from typing import List, Dict
from dataclasses import dataclass
from datetime import datetime
import platform
import logging
from logging.handlers import RotatingFileHandler

from render_object_parts import print_to_console
from settings import domain, media_path, filter_parts, ids


# Настройка логирования в файл
def setup_logger():
    log_file = 'upload_progress.log'
    formatter = logging.Formatter('%(asctime)s | %(message)s')

    # Создаём ротируемый файл логов (максимум 10МБ, сохраняем 5 старых файлов)
    handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    handler.setFormatter(formatter)

    logger = logging.getLogger('upload_progress')
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    return logger


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


class UploadManager:
    def __init__(self, logger, max_concurrent_uploads: int = 10):
        self.semaphore = asyncio.Semaphore(max_concurrent_uploads)
        self.active_uploads = 0
        self.completed_uploads = 0
        self.total_uploads = 0
        self.start_time = None
        self.logger = logger

    async def upload_file(self, session: aiohttp.ClientSession, task: UploadTask) -> bool:
        """Асинхронная загрузка одного файла"""
        async with self.semaphore:
            self.active_uploads += 1
            try:
                # Логируем прогресс
                elapsed = datetime.now() - self.start_time
                progress = (self.completed_uploads / self.total_uploads) * 100
                self.logger.info(
                    f"Progress: {progress:.1f}% | "
                    f"Active: {self.active_uploads} | "
                    f"Completed: {self.completed_uploads}/{self.total_uploads} | "
                    f"Elapsed: {elapsed.seconds}s | "
                    f"File: {os.path.basename(task.file_path)}"
                )

                # Формируем данные для отправки
                data = aiohttp.FormData()
                data.add_field('scene_material', str(task.material_id))
                data.add_field('image',
                               open(task.file_path, 'rb'),
                               filename=os.path.basename(task.file_path))

                async with session.post(f"{domain}/api/product/load_scene_material/",
                                        data=data) as response:
                    success = response.status == 200
                    if success:
                        self.logger.info(f"Successfully uploaded {os.path.basename(task.file_path)}")
                    else:
                        self.logger.error(f"Failed to upload {os.path.basename(task.file_path)}: {response.status}")
                    return success

            except Exception as e:
                self.logger.error(f"Error uploading {task.file_path}: {str(e)}")
                return False
            finally:
                self.active_uploads -= 1
                self.completed_uploads += 1

    async def process_batch(self, tasks: List[UploadTask]) -> List[bool]:
        """Обработка группы задач параллельно"""
        self.total_uploads = len(tasks)
        self.completed_uploads = 0
        self.start_time = datetime.now()

        async with aiohttp.ClientSession() as session:
            upload_tasks = [
                self.upload_file(session, task) for task in tasks
            ]
            return await asyncio.gather(*upload_tasks)


async def process_model_3d(data: Dict, pk: int) -> List[UploadTask]:
    """Подготовка списка задач для загрузки"""
    tasks = []

    for model_n, model_3d in enumerate(data['model_3d'], 1):
        for camera_n, camera in enumerate(model_3d['cameras'], 1):
            for part in camera['parts']:
                blender_name = part['part']['blender_name']

                if len(filter_parts) == 0 or blender_name in filter_parts:
                    dir_name = os.path.join(
                        'variant_%d' % pk,
                        'model_%d' % model_n,
                        'camera_%d' % camera_n,
                        blender_name
                    )

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
    logger = setup_logger()
    upload_manager = UploadManager(logger, max_concurrent_uploads=10)

    logger.info("Starting upload process")

    for product_id in ids:
        try:
            logger.info(f"Processing product {product_id}")

            # Получаем данные о продукте
            async with aiohttp.ClientSession() as session:
                url = f'{domain}/api/product/render/{product_id}/'
                async with session.get(url) as response:
                    if response.status != 200:
                        logger.error(f'Failed to get product data: {response.status}')
                        continue
                    data = await response.json()

            # Подготавливаем задачи для загрузки
            upload_tasks = await process_model_3d(data, product_id)

            if not upload_tasks:
                logger.info(f"No files to upload for product {product_id}")
                continue

            logger.info(f"Starting upload of {len(upload_tasks)} files for product {product_id}")

            # Запускаем параллельную загрузку
            results = await upload_manager.process_batch(upload_tasks)

            # Выводим итоговую статистику
            success_count = sum(1 for r in results if r)
            logger.info(
                f"Completed product {product_id}. "
                f"Successfully uploaded {success_count} of {len(results)} files. "
                f"Time elapsed: {(datetime.now() - upload_manager.start_time).seconds}s"
            )

        except Exception as e:
            logger.error(f"Error processing product {product_id}: {str(e)}")

    logger.info("Upload process completed")


def run_async():
    """Запуск асинхронного кода с учётом особенностей платформы"""
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())


if __name__ == "__main__":
    run_async()