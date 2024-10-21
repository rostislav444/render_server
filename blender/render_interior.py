import os

import bpy
from mathutils import Vector
import requests

from utils.camera import create_camera, get_camera_location
from utils.crete_scene import create_scene
from utils.fetch_object import fetch_and_save_obj
from utils.materials.create import create_material

root = os.path.dirname(os.path.abspath(__file__))
media_path = os.path.join(root, 'media')

local = False
domain = 'http://0.0.0.0:8000' if local else 'http://194.15.46.132:8000'


def GetObjectAndUVMap(obj):
    if obj.type == 'MESH':
        uv_map = obj.data.uv_layers.active
        return obj, uv_map
    return None, None


# Функция для масштабирования 2D-вектора с учетом масштаба и точки опоры
def Scale2D(v, s, p):
    return (p[0] + s[0] * (v[0] - p[0]), p[1] + s[1] * (v[1] - p[1]))


# Функция для масштабирования UV-карты
def ScaleUV(uv_map, scale, pivot):
    for uv_index in range(len(uv_map.data)):
        uv_map.data[uv_index].uv = Scale2D(uv_map.data[uv_index].uv, scale, pivot)


def create_walls_and_floor(depth):
    minus_depth = - depth / 2 / 1000
    size = 20  # Размер плоскостей

    objects_info = [
        {'name': 'pol', 'location': (size / 2 + minus_depth, 0, 0), 'scale': (1, 1, 1)},
        {'name': 'steny_1', 'location': (minus_depth, 0, 20), 'scale': (2, 1, 1), 'rotation': (0, 1.5708, 0)},
    ]

    for obj_info in objects_info:
        # Создание объекта
        bpy.ops.mesh.primitive_plane_add(size=size, enter_editmode=False, align='WORLD', location=obj_info['location'])
        obj = bpy.context.object
        obj.name = obj_info['name']

        # Применение масштаба и поворота, если они указаны
        obj.scale = obj_info.get('scale', (1, 1, 1))
        if 'rotation' in obj_info:
            obj.rotation_euler = obj_info['rotation']

        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)  # Применяем масштаб и поворот

        # Получение объекта и его UV-карты
        obj, uv_map = GetObjectAndUVMap(obj)

        # Если объект найден, масштабируем его UV-карту
        if obj is not None and uv_map is not None:
            pivot = Vector((6, 6))  # Точка опоры для масштабирования
            scale = Vector((6, 6))  # Коэффициент масштабирования UV-карты
            ScaleUV(uv_map, scale, pivot)

        # Возвращаемся в объектный режим
        bpy.ops.object.mode_set(mode='OBJECT')


def send_image(scene_material, image_file_path):
    print('send_image', image_file_path)
    url = domain + '/api/product/load_interior/'
    payload = {'scene_material': scene_material}
    files = {'image': open(image_file_path, 'rb')}
    response = requests.post(url, data=payload, files=files)
    print('response', response.text)
    return response.status_code


def render(filepath):
    bpy.context.scene.render.filepath = filepath
    bpy.ops.render.render(write_still=True)
    return filepath


def apply_holdout_to_scene(exclude_prefix, material):
    # Создаем новый материал для эффекта Holdout
    holdout_material = bpy.data.materials.new(name="Holdout_Material")
    holdout_material.use_nodes = True
    nodes = holdout_material.node_tree.nodes
    links = holdout_material.node_tree.links

    # Удаляем все ноды
    for node in nodes:
        nodes.remove(node)

    # Добавляем Holdout Shader
    holdout_node = nodes.new(type='ShaderNodeHoldout')

    # Создаем выходной узел
    output_node = nodes.new(type='ShaderNodeOutputMaterial')

    # Создаем соединения
    links.new(holdout_node.outputs[0], output_node.inputs[0])

    # Проходим по всем объектам сцены
    for obj in bpy.context.scene.objects:
        # Проверяем, является ли объект мешем и его имя не начинается с указанного префикса
        if obj.type == 'MESH' and not obj.name.startswith(exclude_prefix):
            obj.data.materials.clear()  # Очищаем список материалов объекта
            obj.data.materials.append(holdout_material)
        else:
            if hasattr(obj.data, 'materials'):
                obj.data.materials.clear()
                obj.data.materials.append(material)


def get_file_name(n, slug, material):
    filename = 'camera-%d/%s-%d.png' % (n, slug, material['id'])
    filepath = media_path + '/' + 'image-' + filename
    return filepath


def loop_cameras(product):
    n = 0
    for camera in product['model_3d']['cameras']:
        n += 1
        create_camera(*get_camera_location(camera))

        for interior_layer in camera['interior_layers']:
            slug = interior_layer['slug']
            print('slug', slug)
            for material_group in interior_layer['material_groups']:
                for material in material_group['materials']:
                    mat = create_material(material['material'])
                    filepath = get_file_name(n, slug, material)

                    if os.path.exists(filepath):
                        print('File exists', filepath)
                        continue

                    apply_holdout_to_scene(slug, mat)
                    render(filepath)
                    apply_holdout_to_scene(slug, mat)
                    send_image(material['id'], filepath)


def render_product(data):
    create_scene()
    create_walls_and_floor(data['depth'])
    fetch_and_save_obj(root, data['model_3d']['obj'])
    loop_cameras(data)


def run():
    for i in [13]:
        url = '%s/api/product/interior/%d/' % (domain, i)
        response = requests.get(url)
        if not response.ok:
            print('Response error')
            return

        data = response.json()

        bpy.context.scene.render.resolution_percentage = 100

        render_product(data)


run()
