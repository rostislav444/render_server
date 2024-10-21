import os
from decimal import Decimal
from math import radians

import bpy
import requests

from utils.camera import create_camera, get_camera_location
from utils.crete_scene import create_scene
from utils.fetch_object import fetch_and_save_obj
from utils.materials.fetch import create_materials

root = os.path.dirname(os.path.abspath(__file__))
media_path = os.path.join(root, 'media')

replace = True
local = False
domain = 'http://0.0.0.0:8000' if local else 'http://194.15.46.132:8000'


def send_image(scene_material, image_file_path):
    print('send_image', image_file_path)
    url = domain + '/api/product/load_scene_material/'
    payload = {'scene_material': scene_material}
    files = {'image': open(image_file_path, 'rb')}
    response = requests.post(url, data=payload, files=files)
    print(response.status_code)
    print(response.text)
    return response.status_code


def get_collection_by_name(name):
    for collection in bpy.data.collections:
        if collection.name == name:
            return collection
    return None


def deactivate_holdout_and_apply_material(collection, new_material):
    if isinstance(collection, str):
        collection = get_collection_by_name(collection)

    # Удаляем эффект Holdout из всех материалов объектов коллекции
    for obj in collection.objects:
        if obj.type == 'MESH':
            obj.data.materials.clear()
            obj.data.materials.append(new_material)


def apply_holdout_to_collection(collection):
    if isinstance(collection, str):
        collection = get_collection_by_name(collection)

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

    # Применяем материал ко всем объектам в коллекции
    for obj in collection.objects:
        if obj.type == 'MESH':
            obj.data.materials.clear()  # Очищаем список материалов объекта
            obj.data.materials.append(holdout_material)  # Применяем новый материал


def add_objects_to_collections(parts):
    for part in parts:
        new_collection = bpy.data.collections.new(part['blender_name'])
        bpy.context.scene.collection.children.link(new_collection)

        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH' and obj.name.split('.')[0].lower() == part['blender_name']:
                new_collection.objects.link(obj)


def render(filename=''):
    filepath = media_path + '/' + 'image-' + filename
    bpy.context.scene.render.filepath = filepath
    bpy.ops.render.render(write_still=True)
    return filepath


def loop_part_materials(product):
    n = 0
    for camera in product['model_3d']['cameras']:
        n += 1

        create_camera(*get_camera_location(camera))
        for part in camera['parts']:
            print(part)
            for p in camera['parts']:
                apply_holdout_to_collection(p['part']['blender_name'])

            for material in part['materials']:
                material_id = material['material']
                mat = bpy.data.materials.get(material_id)
                deactivate_holdout_and_apply_material(part['part']['blender_name'], mat)
                if material['image'] is None or replace:
                    filepath = render(part['part']['blender_name'] + '-' + material_id)
                    send_image(material['id'], filepath + '.png')
                    print('Image sent')
                else:
                    print('Image already exists')


def render_product(data):
    create_scene()
    fetch_and_save_obj(root, data['model_3d']['obj'])
    add_objects_to_collections(data['parts'])
    loop_part_materials(data)


def run():
    for i in [17]:
        url = '%s/api/product/render/%d/' % (domain, i)
        print(url)
        response = requests.get(url)
        if not response.ok:
            print('Response error')
            return

        data = response.json()

        bpy.context.scene.render.resolution_percentage = 100

        create_materials(data)
        render_product(data)


run()
