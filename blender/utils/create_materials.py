import os

import bpy
import requests

CURRENT_PATH = os.getcwd()
BASE_URL = 'https://dreamers.s3.eu-north-1.amazonaws.com/'


def check_and_create_dirs(path):
    dirs_to_create = os.path.split(path)[0]

    if not os.path.exists(dirs_to_create):
        os.makedirs(dirs_to_create)


def clear_all():
    bpy.ops.wm.read_homefile(use_empty=True)

    for obj in bpy.context.scene.objects:
        print(obj)


def set_color_material(material, color_rgb):
    principled_bsdf = material.node_tree.nodes.get('Principled BSDF')
    (r, g, b) = color_rgb
    # (r, g, b) = (r / 255, g / 255, b / 255)

    if principled_bsdf:
        principled_bsdf.inputs['Base Color'].default_value = (r, g, b, 1)


def process_texture_response(response, file_name):
    if response.status_code == 200:
        file_content = response.content
        file_path = CURRENT_PATH + '/media/' + file_name

        check_and_create_dirs(file_path)

        with open(file_path, 'wb') as file:
            file.write(file_content)

        texture = bpy.data.images.load(file_path, check_existing=False)
        return texture
    else:
        print(f'Ошибка при загрузке текстуры. Код ответа: {response.status_code}')
        return None


def load_texture(url):
    response = requests.get(BASE_URL + url)
    return process_texture_response(response, url)


def create_texture_node(material, texture):
    texture_node = material.node_tree.nodes.new('ShaderNodeTexImage')
    texture_node.image = texture
    return texture_node


def connect_texture_to_bsdf(material, texture_node, input_name):
    principled_bsdf = material.node_tree.nodes.get('Principled BSDF')
    if principled_bsdf:
        material.node_tree.links.new(principled_bsdf.inputs[input_name], texture_node.outputs['Color'])


def create_material(material_data):
    material = bpy.data.materials.new(name=str(material_data['id']))
    material.use_nodes = True

    if material_data['color']:
        set_color_material(material, material_data['color']['rgb'])
        print('Color created', material_data['color']['name'])
    elif material_data['material']:
        nodes = material.node_tree.nodes
        links = material.node_tree.links

        col = material_data['material']['col']
        nrm = material_data['material'].get('nrm_gl')
        rgh = material_data['material'].get('rgh')
        mtl = material_data['material'].get('mtl')

        base_color = load_texture(col)
        normal_map = load_texture(nrm) if nrm else None
        roughness_map = load_texture(rgh) if rgh else None
        metallic_map = load_texture(mtl) if mtl else None

        # Create the Displacement node
        displacement = nodes.new("ShaderNodeDisplacement")

        # Create the Texture Coordinate node
        tex_coordinate = nodes.new("ShaderNodeTexCoord")

        if base_color:
            base_color_node = create_texture_node(material, base_color)
            links.new(base_color_node.inputs["Vector"], tex_coordinate.outputs["UV"])
            connect_texture_to_bsdf(material, base_color_node, 'Base Color')

        if roughness_map:
            roughness_map_node = create_texture_node(material, roughness_map)
            links.new(roughness_map_node.inputs["Vector"], tex_coordinate.outputs["UV"])
            connect_texture_to_bsdf(material, roughness_map_node, 'Roughness',)

        # if normal_map:
        #     normal_map_node = create_texture_node(material, normal_map)
        #     links.new(normal_map_node.inputs["Vector"], tex_coordinate.outputs["UV"])
        #     connect_texture_to_bsdf(material, normal_map_node, 'Normal')


        # if metallic_map:
        #     metallic_map_node = create_texture_node(material, metallic_map)
        #     # links.new(metallic_map_node.inputs["Vector"], tex_coordinate.outputs["UV"])
        #     connect_texture_to_bsdf(material, metallic_map_node, 'Metallic')


def fetch_and_loop_materials(data):
    for part in data['parts']:
        for material_group in part['material_groups']:
            for material in material_group['materials']:
                create_material(material)

    mat = bpy.data.materials.get('107')


def create_materials(data):
    clear_all()
    fetch_and_loop_materials(data)

