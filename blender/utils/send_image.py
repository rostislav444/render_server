import asyncio
import aiohttp
import aiofiles
from typing import List, Tuple

from settings import domain
import requests

def send_image(scene_material, image_file_path):
    print('send_image', image_file_path)
    url = domain + '/api/product/load_scene_material/'
    payload = {'scene_material': scene_material}
    files = {'image': open(image_file_path, 'rb')}
    response = requests.post(url, data=payload, files=files)
    print(response.status_code)
    print(response.text)
    return response.status_code


# async def send_image_async(scene_material, image_file_path):
#     print('Starting send_image', image_file_path)
#     url = domain + '/api/product/load_scene_material/'
#
#     async with aiofiles.open(image_file_path, 'rb') as file:
#         file_data = await file.read()
#
#     data = aiohttp.FormData()
#     data.add_field('scene_material', str(scene_material))
#     data.add_field('image',
#                    file_data,
#                    filename=image_file_path.split('/')[-1],
#                    content_type='image/png')
#
#     async with aiohttp.ClientSession() as session:
#         async with session.post(url, data=data) as response:
#             print(f'Completed {image_file_path} with status {response.status}')
#             response_text = await response.text()
#             print(response_text)
#             return response.status
#
#
# async def send_multiple_images(image_data: List[Tuple[int, str]]):
#     """
#     Асинхронно отправляет несколько изображений параллельно
#
#     Args:
#         image_data: список кортежей (scene_material, image_file_path)
#     """
#     tasks = [send_image_async(scene_material, path)
#              for scene_material, path in image_data]
#     return await asyncio.gather(*tasks)
#
#
# def send_images_parallel(image_data: List[Tuple[int, str]]):
#     """
#     Синхронная обертка для параллельной отправки изображений
#     """
#     try:
#         loop = asyncio.get_event_loop()
#     except RuntimeError:
#         loop = asyncio.new_event_loop()
#         asyncio.set_event_loop(loop)
#
#     return loop.run_until_complete(send_multiple_images(image_data))
#
#
# # Для обратной совместимости оставляем старую функцию
# def send_image(scene_material, image_file_path):
#     return send_images_parallel([(scene_material, image_file_path)])[0]
