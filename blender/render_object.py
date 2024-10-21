import asyncio
import os
import shutil
from decimal import Decimal
from math import radians

import bpy
import requests

from utils.camera import create_camera
from utils.crete_scene import create_scene
from utils.fetch_object import fetch_and_save_obj
from utils.materials.base import set_color_material

root = '/Users/rostislavnikolaev/Desktop/Sites/render-server/blender'
media_path = os.path.join(root, 'media')

local = False
domain = 'http://0.0.0.0:8000' if local else 'http://194.15.46.132:8000'


def create_new_material(name, color):
    material = bpy.data.materials.new(name=name)
    material.use_nodes = True
    set_color_material(material, color)
    return material


def assign_materials_to_sku(materials):
    black_mat = create_new_material("BlackPaint", [0.05, 0.05, 0.05]),

    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH' and obj.name != 'Exterior':
            obj.data.materials.clear()
            obj_name = obj.name.split('.')[0].lower()

            material_id = materials.get(obj_name, None)
            if material_id:
                mat = bpy.data.materials.get(str(material_id))
            else:
                mat = black_mat[0]

            obj.data.materials.append(mat)


async def send_sku_image(sku, index, image_file_path):
    url = domain + '/api/product/load_sku_images/'

    # Define your payload data
    payload = {
        'sku': sku,
        'index': index
    }

    # Create a dictionary to hold the files to be sent in the request
    files = {'image': open(image_file_path, 'rb')}

    # Send the POST request with the payload and files
    response = requests.post(url, data=payload, files=files)

    # Check the response
    print(response.status_code)
    print(response.text)

    return response.status_code


def delete_dir(dir_path):
    try:
        shutil.rmtree(dir_path)
        print(f"Folder '{dir_path}' and its contents successfully deleted.")
    except OSError as e:
        print(f"Error: {e}")


def loop_sku(sku_list, cameras=None):
    positions = [
        {
            'location': (-3.0024, -1.9402, 0.9089),
            'rotation': (radians(79), 0, radians(-58.4))
        },
        {
            'location': (-3.6307, -0.0045, 0.4650),
            'rotation': (radians(86.49), 0, radians(-89.3))
        },
        {
            'location': (-2.9092, 2.19581, 0.9458),
            'rotation': (radians(78.75), 0, radians(-124.24))
        }
    ] if not cameras else [{
        'location': (Decimal(cam['pos_x']), Decimal(cam['pos_y']), Decimal(cam['pos_z'])),
        'rotation': (radians(Decimal(cam['rad_x'])), radians(Decimal(cam['rad_y'])), radians(Decimal(cam['rad_z'])))
    } for cam in cameras]

    i = 1
    length = len(sku_list)
    for sku in sku_list:
        assign_materials_to_sku(sku['materials'])
        for n, pos in enumerate(positions):
            filepath = media_path + '/' + str(sku['id']) + '/' 'image-' + str(n + 1)
            create_camera(pos['location'], pos['rotation'])
            bpy.context.scene.render.filepath = filepath
            bpy.ops.render.render(write_still=True)
            asyncio.run(send_sku_image(sku['id'], n, f'{filepath}.png'))

        print('%d of %d' % (i, length))
        i += 1

    delete_dir(media_path)


def loop_products(data):
    for product in data['products']:
        create_scene()
        fetch_and_save_obj(root, product['model_3d']['obj'])
        loop_sku(product['sku'], product['model_3d']['cameras'])


def run():
    url = domain + '/api/product/render/2/'
    response = requests.get(url)
    if not response.ok:
        print('Response error')
        return

    data = response.json()

    bpy.context.scene.render.resolution_percentage = 100

    create_materials(data)
    loop_products(data)


run()
