from io import BytesIO
from math import radians

import bpy
import requests

from utils.create_materials import create_materials, set_color_material

root = '/Users/rostislavnikolaev/Desktop/Sites/render-server/blender'
media_path = root + '/media'


def create_new_scene():
    # Clear existing mesh objects in the scene
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_by_type(type='MESH')
    bpy.ops.object.delete()

    # Create a new scene
    new_scene = bpy.data.scenes.new(name="Scene")

    # Link the new scene to the current blend file
    bpy.context.window.scene = new_scene

    # Set the world background color to white
    world = bpy.data.worlds.new(name="World")
    new_scene.world = world
    world.use_nodes = False  # Disable node-based world settings
    world.color = (0.913, 0.861, 0.716)  # Set the background color to white
    # world.color = (0.99, 0.99, 0.99)


def customize_render():
    # Set up render engine
    bpy.context.scene.render.engine = 'CYCLES'

    # Tell blender use GPU
    bpy.context.preferences.addons['cycles'].preferences.compute_device_type = 'METAL'
    # Set the device and feature set
    bpy.context.scene.cycles.device = "GPU"

    # Set samples qty
    bpy.context.scene.cycles.samples = 200

    # Set up rendering settings
    bpy.context.scene.render.resolution_x = 1333
    bpy.context.scene.render.resolution_y = 1000
    bpy.context.scene.render.image_settings.file_format = 'PNG'


def create_camera():
    camera_data = bpy.data.cameras.new(name="Camera")
    camera_object = bpy.data.objects.new("Camera", camera_data)

    # Link the camera object to the scene
    bpy.context.collection.objects.link(camera_object)

    # Set the scene's camera to the newly created camera
    bpy.context.scene.camera = camera_object

    # Optionally, set the camera location and rotation
    camera_object.location = (-3.0024, -1.9402, 0.9089)  # Set the camera position
    camera_object.rotation_euler = (radians(79), 0, radians(-58.4))


def create_light(coords=(8, -4, 8)):
    # Create a new point light object
    light_data = bpy.data.lights.new(name="PointLight", type='POINT')
    light_data.energy = 1  # Set light power in watts
    light_data.shadow_soft_size = 1.0  # Set light radius in centimeters

    light_object = bpy.data.objects.new("PointLight", light_data)

    # Link the light object to the scene
    bpy.context.collection.objects.link(light_object)

    # Set the light location
    light_object.location = coords


def add_cube():
    bpy.ops.mesh.primitive_cube_add(size=200, enter_editmode=False, align='WORLD', location=(0, 0, 100))

    # Select active object
    cube = bpy.context.active_object
    cube.name = "Exterior"

    # Меняем цвет куба на белый
    mat = bpy.data.materials.new(name="White")
    mat.diffuse_color = (1, 1, 1, 1)  # RGBA (белый цвет)
    cube.data.materials.append(mat)


def fetch_and_save_obj(obj_url):
    # Загружаем данные OBJ
    response = requests.get(obj_url)
    obj_data = BytesIO(response.content)

    # Сохраняем данные OBJ в файл
    obj_file_path = root + '/product_3d_obj.obj'
    with open(obj_file_path, 'wb') as obj_file:
        obj_file.write(obj_data.getvalue())

    bpy.ops.wm.obj_import(filepath=obj_file_path, global_scale=1)


def create_material(name, color):
    material = bpy.data.materials.new(name=name)
    material.use_nodes = True
    set_color_material(material, color)
    return material



def create_scene():
    create_new_scene()
    customize_render()
    create_camera()
    # create_light((-6, -6.09, 5.34))


def assign_materials_to_sku(materials):
    black_mat = create_material("BlackPaint", [10, 10, 10]),

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


def loop_sku(sku_list):
    i, j = 0, 0
    length = len(sku_list)
    for sku in sku_list:
        i += 1
        if i < 8000:
            continue
        if j > 3:
            break

        assign_materials_to_sku(sku['materials'])
        bpy.context.scene.render.filepath = media_path + '/' + str(sku['id']) + '/' 'image'
        bpy.ops.render.render(write_still=True)
        j += 1
        print('%d of %d' % (i, length))



def loop_products(data):
    for product in data['products']:
        create_scene()
        fetch_and_save_obj(product['model_3d']['obj'])
        loop_sku(product['sku'])


def run():
    url = 'http://0.0.0.0:8000/api/product/render/1'
    response = requests.get(url)
    data = response.json()

    bpy.context.scene.render.resolution_percentage = 100

    create_materials(data)

    loop_products(data)



run()
