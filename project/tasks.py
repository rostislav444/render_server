from celery import Celery
import bpy

celery_app = Celery('tasks', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')


@celery_app.task(name="create_task")
def create_task(self):
    output_path = "/Users/rostislavnikolaev/Desktop/Sites/render-server/image.png"

    # Set rendering parameters (you can customize these based on your needs)
    bpy.context.scene.render.resolution_x = 1920  # Width of the image
    bpy.context.scene.render.resolution_y = 1080  # Height of the image
    bpy.context.scene.render.image_settings.file_format = 'PNG'  # Output file format
    bpy.context.scene.render.filepath = output_path  # Set the output path

    # Render the image
    bpy.ops.render.render(write_still=True)

    return ''
