from io import BytesIO

import bpy
import requests
import os

from settings import media_path


def fetch_and_save_obj(pk, obj_url):
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_by_type(type='LIGHT')
    bpy.ops.object.select_by_type(type='MESH')
    bpy.ops.object.delete()

    response = requests.get(obj_url)
    if response.status_code == 200:
        obj_file_path = os.path.join(media_path, 'variant_%d' % pk, 'model.obj')

        if not os.path.exists(os.path.dirname(obj_file_path)):
            os.makedirs(os.path.dirname(obj_file_path))

        with open(obj_file_path, 'wb') as obj_file:
            obj_file.write(response.content)

        print(f"File saved successfully at: {obj_file_path}")

        bpy.ops.wm.obj_import(filepath=obj_file_path)
    else:
        print(f"Failed to fetch object from {obj_url}. Status code: {response.status_code}")