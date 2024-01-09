import os
import tempfile

import bpy
import requests
import colorsys

BASE_URL = 'https://dreamers.s3.eu-north-1.amazonaws.com/'


def clear_all():
    bpy.ops.wm.read_homefile(use_empty=True)

    for obj in bpy.context.scene.objects:
        print(obj)


def set_color_material(material, color_rgb):
    principled_bsdf = material.node_tree.nodes.get("Principled BSDF")
    (r, g, b) = color_rgb
    (r, g, b) = (r / 255, g / 255, b / 255)
    (h, s, v) = colorsys.rgb_to_hsv(r, g, b)

    if principled_bsdf:
        principled_bsdf.inputs["Base Color"].default_value = (h, s, v, 1)


def load_texture(url):
    response = requests.get(BASE_URL + url)
    return process_texture_response(response)


def process_texture_response(response):
    if response.status_code == 200:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        temp_file.write(response.content)
        temp_file.close()
        texture = bpy.data.images.load(temp_file.name, check_existing=False)
        os.unlink(temp_file.name)
        return texture
    else:
        print(f"Ошибка при загрузке текстуры. Код ответа: {response.status_code}")
        return None


def create_texture_node(material, texture):
    texture_node = material.node_tree.nodes.new("ShaderNodeTexImage")
    texture_node.image = texture
    return texture_node


def connect_texture_to_bsdf(material, texture_node):
    principled_bsdf = material.node_tree.nodes.get("Principled BSDF")
    if principled_bsdf:
        material.node_tree.links.new(principled_bsdf.inputs['Base Color'], texture_node.outputs['Color'])


def create_material(material_data):
    material = bpy.data.materials.new(name=str(material_data["id"]))
    material.use_nodes = True

    if material_data["color"]:
        set_color_material(material, material_data["color"]["rgb"])
        print('Color created', material_data['color']['name'])
    elif material_data["material"]:
        texture = load_texture(material_data["material"]["col"])
        if texture:
            texture_node = create_texture_node(material, texture)
            connect_texture_to_bsdf(material, texture_node)
        print('Material created', material_data, material_data['material']['name'])

    return 'material'


def fetch_and_loop_materials(data):
    for part in data['parts']:
        for material_group in part['material_groups']:
            for material in material_group['materials']:
                create_material(material)

    mat = bpy.data.materials.get('107')
    print(mat)


def create_materials(data):
    clear_all()
    fetch_and_loop_materials(data)
