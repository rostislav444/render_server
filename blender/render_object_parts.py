import json
import os

import bpy
import requests

from settings import domain, replace, root, media_path
from utils.camera import create_camera, get_camera_location
from utils.crete_scene import create_scene
from utils.fetch_object import fetch_and_save_obj
from utils.materials.fetch import create_materials
from utils.send_image import send_image


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

    file_data[variant_key][model_key][camera_key].append(new_data)

    with open(file_name, 'w') as file:
        json.dump(file_data, file, indent=4)


def loop_part_materials(pk, model_n, model_3d):
    for n, camera in enumerate(model_3d['cameras'], 1):
        create_camera(*get_camera_location(camera))
        for part in camera['parts']:
            dir_name = os.path.join('variant_%d' % pk, 'model_%d' % model_n, 'camera_%d' % n,
                                    part['part']['blender_name'])
            media_dir = os.path.join(media_path, str(dir_name))
            if not os.path.exists(media_dir):
                os.makedirs(media_dir)

            for p in camera['parts']:
                apply_holdout_to_collection(p['part']['blender_name'])

            for material in part['materials']:
                material_id = material['material']
                mat = bpy.data.materials.get(material_id)

                deactivate_holdout_and_apply_material(part['part']['blender_name'], mat)
                filepath = dir_name + '/' + material_id + '.png'
                media_filepath = os.path.join(media_path, filepath)

                if material['image'] is None or replace:
                    render(filepath)
                    send_image(material['id'], media_filepath)
                    write_to_json(pk, model_n, n, material['id'], filepath)
                else:
                    print('Image already exists')


def render_product(data, pk):
    create_scene()
    for model_n, model_3d in enumerate(data['model_3d'], 1):
        fetch_and_save_obj(pk, model_3d['obj'])
        add_objects_to_collections(data['parts'])
        loop_part_materials(pk, model_n, model_3d)


def run():
    for i in [2]:
        url = '%s/api/product/render/%d/' % (domain, i)
        response = requests.get(url)
        if not response.ok:
            print('Response error')
            return

        data = response.json()

        bpy.context.scene.render.resolution_percentage = 100

        create_materials(data)
        render_product(data, i)


run()
