import bpy
from math import radians


output_path = '/Users/rostislavnikolaev/Desktop/Sites/render-server/blender/image'


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
    world.color = (0, 0, 0)  # Set the background color to white


def customize_render():
    # # Set up render engine
    # bpy.context.scene.render.engine = 'CYCLES'
    #
    # # Tell blender use GPU
    # bpy.context.preferences.addons['cycles'].preferences.compute_device_type = 'METAL'
    #
    # # Set samples qty
    # bpy.context.scene.cycles.samples = 1000

    # Set up rendering settings
    bpy.context.scene.render.resolution_x = 1920
    bpy.context.scene.render.resolution_y = 1080
    bpy.context.scene.render.image_settings.file_format = 'PNG'
    bpy.context.scene.render.filepath = output_path


def create_camera():
    camera_data = bpy.data.cameras.new(name="Camera")
    camera_object = bpy.data.objects.new("Camera", camera_data)

    # Link the camera object to the scene
    bpy.context.collection.objects.link(camera_object)

    # Set the scene's camera to the newly created camera
    bpy.context.scene.camera = camera_object

    # Optionally, set the camera location and rotation
    camera_object.location = (2.5, -2.5, 1.3)  # Set the camera position
    camera_object.rotation_euler = (radians(72), 0, radians(43))


def create_light(coords=(7, -3, 5)):
    # Create a new point light object
    light_data = bpy.data.lights.new(name="PointLight", type='POINT')
    light_data.energy = 4000  # Set light power in watts
    light_data.shadow_soft_size = 1.0  # Set light radius in centimeters

    light_object = bpy.data.objects.new("PointLight", light_data)

    # Link the light object to the scene
    bpy.context.collection.objects.link(light_object)

    # Set the light location
    light_object.location = coords



def create_scene():
    create_new_scene()
    customize_render()
    create_camera()
    create_light()
    create_light((-7, -3, 5))

