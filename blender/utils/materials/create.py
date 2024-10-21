import json
from decimal import Decimal

import bpy

from utils.materials.base import load_texture


def connect_texture_to_bsdf(material, texture_node, input_name):
    principled_bsdf = material.node_tree.nodes.get('Principled BSDF')
    if principled_bsdf:
        material.node_tree.links.new(principled_bsdf.inputs[input_name], texture_node.outputs['Color'])


def create_texture_node(material, texture):
    texture_node = material.node_tree.nodes.new('ShaderNodeTexImage')
    texture_node.image = texture
    return texture_node


def set_color_to_material(material, color_rgb):
    principled_bsdf = material.node_tree.nodes.get('Principled BSDF')
    (r, g, b) = color_rgb

    if principled_bsdf:
        principled_bsdf.inputs['Base Color'].default_value = (r, g, b, 1)


def create_texture_material(material, blender_material):
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    scale = Decimal(blender_material['scale'])
    ratio = Decimal(blender_material['aspect_ratio'])
    if ratio > 1:
        # Горизонтальная картинка: ширина больше высоты
        scale_x = scale * ratio
        scale_y = scale
    else:
        # Вертикальная картинка: высота больше ширины
        scale_x = scale
        scale_y = scale / ratio

    if not blender_material:
        raise ValueError('blender_material is None')

    # Загружаем необходимые текстуры
    col = blender_material['col']
    base_color = load_texture(col)

    nrm_gl = blender_material.get('nrm_gl')
    normal_map = load_texture(nrm_gl) if nrm_gl else None

    rgh = blender_material.get('rgh')
    roughness_map = load_texture(rgh) if rgh else None

    mtl = blender_material.get('mtl')
    metallic_map = load_texture(mtl) if mtl else None

    disp = blender_material.get('disp')
    displacement_map = load_texture(disp) if disp else None

    bump = blender_material.get('bump')
    bump_map = load_texture(bump) if bump else None

    ao = blender_material.get('ao')
    ao_map = load_texture(ao) if ao else None

    # Создаем узлы
    tex_coordinate = nodes.new("ShaderNodeTexCoord")
    mapping_node = nodes.new("ShaderNodeMapping")

    mapping_node.inputs['Scale'].default_value = (scale_x, scale_y, scale)
    links.new(mapping_node.inputs["Vector"], tex_coordinate.outputs["UV"])

    displacement_node = nodes.new("ShaderNodeDisplacement")

    if base_color:
        base_color_node = create_texture_node(material, base_color)
        links.new(base_color_node.inputs["Vector"], mapping_node.outputs["Vector"])
        connect_texture_to_bsdf(material, base_color_node, 'Base Color')
        print('Base color created')

    if roughness_map:
        roughness_map_node = create_texture_node(material, roughness_map)
        links.new(roughness_map_node.inputs["Vector"], mapping_node.outputs["Vector"])
        connect_texture_to_bsdf(material, roughness_map_node, 'Roughness')
        print('Roughness created')

    if normal_map:
        normal_map_node = create_texture_node(material, normal_map)
        links.new(normal_map_node.inputs["Vector"], mapping_node.outputs["Vector"])
        connect_texture_to_bsdf(material, normal_map_node, 'Normal')
        print('Normal created')

    if metallic_map:
        metallic_map_node = create_texture_node(material, metallic_map)
        links.new(metallic_map_node.inputs["Vector"], mapping_node.outputs["Vector"])
        connect_texture_to_bsdf(material, metallic_map_node, 'Metallic')
        print('Metallic created')

    if displacement_map:
        displacement_map_node = create_texture_node(material, displacement_map)
        links.new(displacement_map_node.inputs["Vector"], mapping_node.outputs["Vector"])
        links.new(displacement_node.inputs["Height"], displacement_map_node.outputs["Color"])
        links.new(displacement_node.outputs["Displacement"],
                  material.node_tree.nodes['Material Output'].inputs['Displacement'])
        print('Displacement created')

    if bump_map:
        bump_map_node = create_texture_node(material, bump_map)
        links.new(bump_map_node.inputs["Vector"], mapping_node.outputs["Vector"])
        bump_node = nodes.new("ShaderNodeBump")
        links.new(bump_node.inputs["Height"], bump_map_node.outputs["Color"])
        links.new(bump_node.outputs["Normal"], material.node_tree.nodes['Principled BSDF'].inputs['Normal'])
        print('Bump created')

    if ao_map:
        ao_map_node = create_texture_node(material, ao_map)
        links.new(ao_map_node.inputs["Vector"], mapping_node.outputs["Vector"])

        # Создаем узел MixRGB для умножения карты AO на Base Color
        mix_rgb_node = nodes.new("ShaderNodeMixRGB")
        mix_rgb_node.blend_type = 'MULTIPLY'
        mix_rgb_node.inputs['Fac'].default_value = 0.35

        # Привязываем AO карту к MixRGB узлу
        links.new(mix_rgb_node.inputs[2], ao_map_node.outputs["Color"])

        # Привязываем Base Color к MixRGB узлу
        base_color_node = create_texture_node(material, base_color)
        links.new(base_color_node.inputs["Vector"], mapping_node.outputs["Vector"])
        links.new(mix_rgb_node.inputs[1], base_color_node.outputs['Color'])

        # Результат MixRGB направляем в Base Color узла Principled BSDF
        links.new(mix_rgb_node.outputs['Color'], material.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
        print('Ambient Occlusion integrated')

    return material


def create_material(material_data):
    material = bpy.data.materials.new(name=str(material_data['id']))
    material.use_nodes = True

    if material_data.get('color'):
        set_color_to_material(material, material_data['color']['rgb'])
        print('Color created', material_data['color']['name'])

    elif material_data.get('material'):
        print(json.dumps(material_data['material'], indent=4))
        material = create_texture_material(material, material_data['material']['blender_material'])
        print('Material created', material_data['material']['name'])

    return material
