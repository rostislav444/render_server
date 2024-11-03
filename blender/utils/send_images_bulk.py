import asyncio
import aiohttp
import aiofiles
import json
from typing import List, Tuple

from settings import domain

# Глобальный список для хранения задач
image_queue = []


def send_image(scene_material, image_file_path):
    """Добавляет изображение в очередь для отправки"""
    image_queue.append((scene_material, image_file_path))
    print(f"Added to queue: {image_file_path}")


async def send_image_async(scene_material, image_file_path):
    """Отправляет одно изображение"""
    print('Sending:', image_file_path)
    url = domain + '/api/product/load_scene_material/'

    async with aiofiles.open(image_file_path, 'rb') as file:
        file_data = await file.read()

    data = aiohttp.FormData()
    data.add_field('scene_material', str(scene_material))
    data.add_field('image',
                   file_data,
                   filename=image_file_path.split('/')[-1],
                   content_type='image/png')

    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data) as response:
            print(f'Completed: {image_file_path}')
            return response.status


async def process_all_images():
    """Асинхронно отправляет все изображения из очереди"""
    if not image_queue:
        print("Queue is empty")
        return

    tasks = [send_image_async(mat, path) for mat, path in image_queue]
    results = await asyncio.gather(*tasks)

    # Очищаем очередь после отправки
    image_queue.clear()

    return results


def send_all_images():
    """Синхронная обертка для отправки всех изображений"""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(process_all_images())