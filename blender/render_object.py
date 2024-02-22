import shutil
from io import BytesIO
from math import radians
import asyncio
import bpy
import requests
from decimal import Decimal
from utils.create_materials import create_materials, set_color_material

root = '/Users/rostislavnikolaev/Desktop/Sites/render-server/blender'
media_path = root + '/media'

local = False
domain = 'http://0.0.0.0:8000' if local else 'https://dreamers.com.ua'


def create_new_scene():
    # Clear existing mesh objects in the scene
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_by_type(type='LIGHT')
    bpy.ops.object.select_by_type(type='MESH')
    bpy.ops.object.delete()

    # Create a new scene
    new_scene = bpy.data.scenes.new(name="Scene")
    # new_scene.shading.use_scene_lights_render = True
    # new_scene.shading.use_scene_world_render = True

    # Link the new scene to the current blend file
    bpy.context.window.scene = new_scene

    # Set the world background color to white
    world = bpy.data.worlds.new(name="World")
    new_scene.world = world
    world.use_nodes = False
    world.color = (1, 1, 1)


def customize_render():
    # Set up render engine
    bpy.context.scene.render.engine = 'CYCLES'

    # Tell blender use GPU
    bpy.context.preferences.addons['cycles'].preferences.compute_device_type = 'METAL'

    # Set samples qty
    bpy.context.scene.cycles.samples = 200

    # Set up rendering settings
    bpy.context.scene.render.resolution_x = 1333
    bpy.context.scene.render.resolution_y = 1000
    bpy.context.scene.render.image_settings.file_format = 'PNG'
    bpy.context.scene.render.film_transparent = True


def create_camera(location, rotation):
    # Удаляем все камеры в сцене
    for obj in bpy.context.scene.objects:
        if obj.type == 'CAMERA':
            bpy.data.objects.remove(obj, do_unlink=True)

    # Создаем новую камеру
    camera_data = bpy.data.cameras.new(name="Camera")
    camera_object = bpy.data.objects.new("Camera", camera_data)

    # Link the camera object to the scene
    bpy.context.collection.objects.link(camera_object)

    # Set the scene's camera to the newly created camera
    bpy.context.scene.camera = camera_object

    # Optionally, set the camera location and rotation
    camera_object.location = location
    camera_object.rotation_euler = rotation


def create_light(coords=(8, -4, 8)):
    # Create a new point light object
    light_data = bpy.data.lights.new(name="PointLight", type='POINT')
    light_data.energy = 2000  # Set light power in watts
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
    create_light((4.07, 1.02, 5.8))


def assign_materials_to_sku(materials):
    black_mat = create_material("BlackPaint", [0.05, 0.05, 0.05]),

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
        fetch_and_save_obj(product['model_3d']['obj'])
        print(product['model_3d']['cameras'])
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
