import os

import bpy
import requests

CURRENT_PATH = os.getcwd()



def check_and_create_dirs(path):
    dirs_to_create = os.path.split(path)[0]

    if not os.path.exists(dirs_to_create):
        os.makedirs(dirs_to_create)


def clear_all():
    bpy.ops.wm.read_homefile(use_empty=True)

    for obj in bpy.context.scene.objects:
        print(obj)


def set_color_material(material, color_rgb):
    principled_bsdf = material.node_tree.nodes.get('Principled BSDF')
    (r, g, b) = color_rgb
    # (r, g, b) = (r / 255, g / 255, b / 255)

    if principled_bsdf:
        principled_bsdf.inputs['Base Color'].default_value = (r, g, b, 1)


def process_texture_response(response, file_path):
    if response.status_code == 200:
        file_content = response.content

        # Проверяем и создаем директории, если нужно
        if not os.path.exists(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))

        # Сохраняем файл на диск
        with open(file_path, 'wb') as file:
            file.write(file_content)

        # Загружаем текстуру в Blender
        texture = bpy.data.images.load(file_path, check_existing=False)
        return texture
    else:
        print(f'Ошибка при загрузке текстуры. Код ответа: {response.status_code}')
        return None


def load_texture(url):
    # Получаем имя файла из URL
    file_name = url.split('/')[-1]
    # Формируем полный путь к файлу
    file_path = os.path.join(CURRENT_PATH, 'media/materials', file_name)

    # Проверяем, существует ли файл
    if os.path.exists(file_path):
        print(f'Файл уже существует: {file_path}')
        # Загружаем текстуру из существующего файла в Blender
        texture = bpy.data.images.load(file_path, check_existing=False)
        return texture
    else:
        # Если файл не существует, загружаем его
        response = requests.get(url)
        return process_texture_response(response, file_path)
