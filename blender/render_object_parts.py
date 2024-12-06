import json
import os

import bpy
import requests

from settings import domain, media_path
from utils.camera import create_camera, get_camera_location
from utils.crete_scene import create_scene, create_hdr_scene
from utils.fetch_object import fetch_and_save_obj
from utils.materials.fetch import create_materials
from utils.send_image import send_image

filter_parts = []
manual_ids = []

write_anyway = True
make_render = input('Render? (y/n): ') == 'y'
ids = manual_ids if len(manual_ids) > 0 else [int(i) for i in input('Enter ids: ').replace(' ', '').split(',')]
hdr = True


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
    # Удаляем все существующие коллекции, кроме коллекции по умолчанию
    for collection in bpy.data.collections:
        if collection.name != "Collection":
            bpy.data.collections.remove(collection)

    for part in parts:
        new_collection = bpy.data.collections.new(part['blender_name'])
        bpy.context.scene.collection.children.link(new_collection)

        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH' and obj.name.split('.')[0].lower() == part['blender_name']:
                new_collection.objects.link(obj)


def render(filepath):
    bpy.context.scene.render.filepath = filepath
    bpy.ops.render.render(write_still=True)


def write_to_json(pk, model_n, camera_n, material_id, file_path):
    file_name = os.path.join(media_path, 'variant_%d' % pk, 'images.json')
    new_data = [material_id, file_path]

    if not os.path.exists(file_name):
        with open(file_name, 'w') as file:
            json.dump({}, file)
            file_data = {}
    else:
        with open(file_name, 'r') as file:
            file_data = json.load(file)

    variant_key = "variant_%d" % pk
    model_key = "model_%d" % model_n
    camera_key = "camera_%d" % camera_n

    if variant_key not in file_data:
        file_data[variant_key] = {}

    if model_key not in file_data[variant_key]:
        file_data[variant_key][model_key] = {}

    if camera_key not in file_data[variant_key][model_key]:
        file_data[variant_key][model_key][camera_key] = []

    if new_data not in file_data[variant_key][model_key][camera_key]:
        file_data[variant_key][model_key][camera_key].append(new_data)

    with open(file_name, 'w') as file:
        json.dump(file_data, file, indent=4)


def print_to_console(rendering, pk, blender_name, model_n, camera_n, camera_count, material_n, materials_count):
    action = 'Rendering' if rendering else 'Sending'

    print('\n' * 3)
    print('*' * 50)
    print('\n%s id%d: %s' % (action, pk, blender_name.upper()))
    print('Model %d' % model_n)
    print('Camera %d of %d' % (camera_n, camera_count))
    print('Material %d of %d\n' % (material_n, materials_count))
    print('*' * 50)
    print('\n' * 3)


def render_part_materials(pk, model_n, model_3d):
    for n, camera in enumerate(model_3d['cameras'], 1):
        create_camera(*get_camera_location(camera))
        for part in camera['parts']:
            blender_name = part['part']['blender_name']

            if len(filter_parts) == 0 or blender_name in filter_parts:
                print('Rendering', blender_name)

                dir_name = os.path.join('variant_%d' % pk, 'model_%d' % model_n, 'camera_%d' % n, blender_name)
                media_dir = os.path.join(media_path, str(dir_name))
                if not os.path.exists(media_dir):
                    os.makedirs(media_dir)

                for p in camera['parts']:
                    apply_holdout_to_collection(p['part']['blender_name'])

                materials_count = len(part['materials'])
                for material_n, material in enumerate(part['materials'], 1):
                    print_to_console(True, pk, blender_name, model_n, n, len(model_3d['cameras']), material_n,
                                     materials_count)

                    material_id = material['material']
                    mat = bpy.data.materials.get(material_id)

                    deactivate_holdout_and_apply_material(part['part']['blender_name'], mat)
                    filepath = dir_name + '/' + material_id + '.png'
                    media_filepath = os.path.join(media_path, filepath)

                    if write_anyway or (not os.path.exists(media_filepath) and material['image'] is None):
                        render(media_filepath)
                        write_to_json(pk, model_n, n, material_id, filepath)


def render_product(data, pk):
    create_scene()

    for model_n, model_3d in enumerate(data['model_3d'], 1):
        fetch_and_save_obj(pk, model_3d['obj'])
        add_objects_to_collections(data['parts'])
        render_part_materials(pk, model_n, model_3d)


def send_part_materials(pk, model_n, model_3d):
    for n, camera in enumerate(model_3d['cameras'], 1):
        for part in camera['parts']:
            blender_name = part['part']['blender_name']

            if len(filter_parts) == 0 or blender_name in filter_parts:
                dir_name = os.path.join('variant_%d' % pk, 'model_%d' % model_n, 'camera_%d' % n, blender_name)

                materials_count = len(part['materials'])
                for material_n, material in enumerate(part['materials'], 1):
                    print_to_console(False, pk, blender_name, model_n, n, len(model_3d['cameras']), material_n,
                                     materials_count)

                    material_id = material['material']
                    filepath = dir_name + '/' + material_id + '.png'
                    media_filepath = os.path.join(media_path, filepath)

                    if os.path.exists(media_filepath) and material['image'] is None:
                        try:
                            send_image(material['id'], media_filepath)
                        except requests.exceptions.ConnectionError:
                            print('Connection error')
                            send_image(material['id'], media_filepath)
                    else:
                        print(os.path.exists(media_filepath), material['image'])




def send_product(data, pk):
    for model_n, model_3d in enumerate(data['model_3d'], 1):
        send_part_materials(pk, model_n, model_3d)


def run():
    for i in manual_ids:
        url = '%s/api/product/render/%d/' % (domain, i)
        response = requests.get(url)
        if not response.ok:
            print('Response error')
            return

        data = response.json()

        if make_render:
            bpy.context.scene.render.resolution_percentage = 100
            create_materials(data)
            render_product(data, i)
        else:
            send_product(data, i)


run()
