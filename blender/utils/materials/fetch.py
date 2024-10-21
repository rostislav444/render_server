from utils.materials.base import clear_all
from utils.materials.create import create_material


def fetch_and_loop_materials(data):
    for part in data['parts']:
        print(part)
        for material_group in part['material_groups']:
            for material in material_group['materials']:
                create_material(material)


def create_materials(data):
    clear_all()
    fetch_and_loop_materials(data)