import bpy
import math
import mathutils

MEDIA_DIR = '/Users/rostislavnikolaev/Desktop/render'
camera = bpy.data.objects["Camera"]

def get_rotation_coordiantes(steps=12, radius=4, z=2):
    result = []
    if steps > 360:
        steps = 360
    step = 120 / steps

    for i in range(steps):
        angle = 45 + i * step
        x = radius * math.sin(math.radians(angle))
        y = radius * math.cos(math.radians(angle))

        rotation = math.pi
        if angle > 0:
            rotation -= math.pi * 2 * angle / 360

        result.append({
            'location': (x, y, z),
            'angle': (math.pi * 0.40, 0, rotation)
        })
    return result


coordinates = get_rotation_coordiantes(8)

# index = 4
# camera.location = mathutils.Vector(coordinates[index]['location'])
# camera.rotation_euler = coordinates[index]['angle']

scene = bpy.context.scene

for i, coordinate in enumerate(coordinates):
    # set camera
    camera.location = mathutils.Vector(coordinate['location'])
    camera.rotation_euler = coordinate['angle']
    scene.camera = camera

    # render
    scene.render.image_settings.file_format = 'JPEG'
    scene.render.filepath = MEDIA_DIR + f'blender/image_{i}.jpeg'
    bpy.ops.render.render(write_still=1)