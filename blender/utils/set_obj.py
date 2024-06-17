from io import BytesIO

import bpy
import requests

output_path = '/Users/rostislavnikolaev/Desktop/Sites/render-server/blender/image'
obj_url = 'http://127.0.0.1:8000/media/product3dblendermodel/tumba-tumba_w140_h45_d55_3d.obj'


def add_cube():
    bpy.ops.mesh.primitive_cube_add(size=20, enter_editmode=False, align='WORLD', location=(4, -20, 10))

    # Select active object
    cube = bpy.context.active_object

    # Меняем цвет куба на белый
    mat = bpy.data.materials.new(name="White")
    mat.diffuse_color = (1, 1, 1, 1)  # RGBA (белый цвет)
    cube.data.materials.append(mat)




def fetch_and_save_obj():
    # Загружаем данные OBJ
    response = requests.get(obj_url)
    obj_data = BytesIO(response.content)

    # Сохраняем данные OBJ в файл
    obj_file_path = output_path + '.obj'
    with open(obj_file_path, 'wb') as obj_file:
        obj_file.write(obj_data.getvalue())

    bpy.ops.wm.obj_import(filepath=obj_file_path, global_scale=1)

    add_cube()




