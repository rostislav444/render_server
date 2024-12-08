import os

import requests

from render_object_parts import print_to_console
from settings import domain, media_path, filter_parts
from utils.send_image import send_image


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
    for i in ids:
        url = '%s/api/product/render/%d/' % (domain, i)
        response = requests.get(url)
        if not response.ok:
            print('Response error')
            return

        data = response.json()
        send_product(data, i)


run()
