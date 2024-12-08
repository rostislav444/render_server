import requests

from settings import domain


def send_image(scene_material, image_file_path):
    print('send_image', image_file_path)
    url = domain + '/api/product/load_scene_material/'
    payload = {'scene_material': scene_material}
    files = {'image': open(image_file_path, 'rb')}
    response = requests.post(url, data=payload, files=files)
    print(response.status_code)
    print(response.text)
    return response.status_code
