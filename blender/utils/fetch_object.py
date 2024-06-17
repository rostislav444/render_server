from io import BytesIO

import bpy
import requests


def fetch_and_save_obj(root, obj_url):
    response = requests.get(obj_url)
    obj_data = BytesIO(response.content)

    obj_file_path = root + '/product_3d_obj.obj'
    with open(obj_file_path, 'wb') as obj_file:
        obj_file.write(obj_data.getvalue())

    bpy.ops.wm.obj_import(filepath=obj_file_path, global_scale=1)
