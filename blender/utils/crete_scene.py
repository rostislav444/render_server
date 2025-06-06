import bpy
import platform

import settings


hdri_path = 'recources/world.exr'


def create_hdr_scene():
    rad = 0.0174533
    grad = -70
    # Create new world if it doesn't exist
    if not bpy.context.scene.world:
        world = bpy.data.worlds.new(name="World")
        bpy.context.scene.world = world
        world.use_nodes = True

    # Get world node tree
    world_node_tree = bpy.context.scene.world.node_tree
    world_node_tree.nodes.clear()

    location_x = 0

    # Add Texture Coordinate node
    tex_coord = world_node_tree.nodes.new('ShaderNodeTexCoord')
    tex_coord.location.x = location_x
    # location_x += 300

    # Add Mapping node
    mapping_node = world_node_tree.nodes.new('ShaderNodeMapping')
    mapping_node.location.x = location_x
    mapping_node.inputs['Location'].default_value = (0, 0, 0)
    # 1 grad = 0.0174533 rad

    mapping_node.inputs['Rotation'].default_value = (0, 0, rad * grad)
    mapping_node.inputs['Scale'].default_value = (1.0, 1.0, 1.0)
    # location_x += 300

    # Add Environment Texture node
    environment_texture_node = world_node_tree.nodes.new(type="ShaderNodeTexEnvironment")
    environment_texture_node.image = bpy.data.images.load(hdri_path)
    environment_texture_node.location.x = location_x
    environment_texture_node.interpolation = 'Linear'
    environment_texture_node.projection = 'EQUIRECTANGULAR'
    environment_texture_node.image.colorspace_settings.name = 'Linear Rec.709'
    # location_x += 300

    # Add Background node
    background_node = world_node_tree.nodes.new(type="ShaderNodeBackground")
    background_node.inputs["Strength"].default_value = 0.8
    background_node.location.x = location_x
    # location_x += 300

    # Add Output node
    world_output_node = world_node_tree.nodes.new(type="ShaderNodeOutputWorld")
    world_output_node.location.x = location_x

    # Link nodes
    links = world_node_tree.links
    links.new(tex_coord.outputs["Window"], mapping_node.inputs["Vector"])  # Changed to "Window"
    links.new(mapping_node.outputs["Vector"], environment_texture_node.inputs["Vector"])
    links.new(environment_texture_node.outputs["Color"], background_node.inputs["Color"])
    links.new(background_node.outputs["Background"], world_output_node.inputs["Surface"])


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

    # Set the render anti-aliasing to off
    bpy.context.scene.display.render_aa = 'OFF'

    # Set the world background color to white
    world = bpy.data.worlds.new(name="World")
    new_scene.world = world
    world.use_nodes = False
    world.color = (1, 1, 1)


def customize_render():
    size = 1 * 0.65
    bpy.context.scene.render.engine = 'CYCLES'

    bpy.context.preferences.addons['cycles'].preferences.refresh_devices()

    gpu_devices = [d for d in bpy.context.preferences.addons['cycles'].preferences.devices if d.type != 'CPU']
    
    print("Найденные GPU устройства:")
    for d in gpu_devices:
        print(f"  {d.name}, type: {d.type}")

    if not gpu_devices:
        raise RuntimeError("Не найдено ни одного GPU устройства! Рендеринг на CPU запрещен.")

    bpy.context.scene.cycles.device = 'GPU'

    optix_devices = [d for d in gpu_devices if d.type == 'OPTIX']
    metal_devices = [d for d in gpu_devices if d.type == 'METAL']
    cuda_devices = [d for d in gpu_devices if d.type == 'CUDA']

    if optix_devices:
        print("Используем OPTIX устройства (самый быстрый вариант)")
        bpy.context.preferences.addons['cycles'].preferences.compute_device_type = 'OPTIX'
        for device in optix_devices:
            device.use = True
            print(f"  Включено: {device.name}")
        
        available_denoisers = list(bpy.context.scene.cycles.bl_rna.properties['denoiser'].enum_items.keys())
        if 'OPTIX' in available_denoisers:
            bpy.context.scene.cycles.denoiser = 'OPTIX'
            print("  Деноизер: OPTIX (лучший для NVIDIA)")
        elif 'OPENIMAGEDENOISE' in available_denoisers:
            bpy.context.scene.cycles.denoiser = 'OPENIMAGEDENOISE'
            print("  Деноизер: OpenImageDenoise")

    elif metal_devices:
        print("Используем METAL устройства (Apple)")
        bpy.context.preferences.addons['cycles'].preferences.compute_device_type = 'METAL'
        for device in metal_devices:
            device.use = True
            print(f"  Включено: {device.name}")
        
        available_denoisers = list(bpy.context.scene.cycles.bl_rna.properties['denoiser'].enum_items.keys())
        if 'OPENIMAGEDENOISE' in available_denoisers:
            bpy.context.scene.cycles.denoiser = 'OPENIMAGEDENOISE'
            print("  Деноизер: OpenImageDenoise")

    elif cuda_devices:
        print("Используем CUDA устройства")
        bpy.context.preferences.addons['cycles'].preferences.compute_device_type = 'CUDA'
        for device in cuda_devices:
            device.use = True
            print(f"  Включено: {device.name}")
        
        available_denoisers = list(bpy.context.scene.cycles.bl_rna.properties['denoiser'].enum_items.keys())
        if 'OPENIMAGEDENOISE' in available_denoisers:
            bpy.context.scene.cycles.denoiser = 'OPENIMAGEDENOISE'
            print("  Деноизер: OpenImageDenoise")

    bpy.context.preferences.addons['cycles'].preferences.refresh_devices()

    bpy.context.scene.cycles.samples = 200

    bpy.context.scene.render.resolution_x = int(3000 * size)
    bpy.context.scene.render.resolution_y = int(2000 * size)
    bpy.context.scene.render.image_settings.file_format = 'PNG'
    bpy.context.scene.render.film_transparent = True


def create_light(coords=(8, -4, 8)):
    # Create a new point light object
    light_data = bpy.data.lights.new(name="PointLight", type='POINT')
    light_data.energy = 3500  # Set light power in watts
    light_data.shadow_soft_size = 8.0  # Set light radius in centimeters
    light_data.color = (1, 0.949, 0.864)

    light_object = bpy.data.objects.new("PointLight", light_data)

    # Link the light object to the scene
    bpy.context.collection.objects.link(light_object)

    # Set the light location
    light_object.location = coords


def create_scene():
    bpy.context.scene.render.film_transparent = True
    bpy.context.scene.render.filter_size = 1.5
    bpy.context.scene.cycles.blur_glossy = 0

    customize_render()
    create_hdr_scene()

    # create_light((4.07, 1.02, 5.8))
