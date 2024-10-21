import bpy


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
    size = 1 * 0.9
    # Set up render engine
    bpy.context.scene.render.engine = 'CYCLES'

    # Tell blender use GPU
    bpy.context.preferences.addons['cycles'].preferences.compute_device_type = 'METAL'
    bpy.context.scene.cycles.device = 'GPU'
    bpy.context.preferences.addons['cycles'].preferences.refresh_devices()
    for d in bpy.context.preferences.addons['cycles'].preferences.devices:
        print(d)
    bpy.context.preferences.addons['cycles'].preferences.devices['Apple M1 (GPU - 7 cores)'].use = True

    # Set samples qty
    bpy.context.scene.cycles.samples = 200

    # Set up rendering settings
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
    create_new_scene()
    customize_render()
    create_light((4.07, 1.02, 5.8))
