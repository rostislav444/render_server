from io import BytesIO

import bpy
import requests
import os


def fetch_and_save_obj(root, obj_url):
    response = requests.get(obj_url)
    if response.status_code == 200:
        obj_file_path = os.path.join(root, 'product_3d_obj.obj')
        with open(obj_file_path, 'wb') as obj_file:
            obj_file.write(response.content)

        print(f"File saved successfully at: {obj_file_path}")

        bpy.ops.wm.obj_import(filepath=obj_file_path)
    else:
        print(f"Failed to fetch object from {obj_url}. Status code: {response.status_code}")