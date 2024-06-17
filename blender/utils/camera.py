import bpy


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
