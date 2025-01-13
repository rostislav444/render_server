import bpy
import json
from mathutils import Vector
import re

def get_base_name(name):
    return re.split(r'\.\d+', name)[0]

def get_dimensions_and_copies(obj):
    if obj.name not in bpy.context.view_layer.objects:
        # Если объект не в текущем view_layer, просто возвращаем его размеры
        dims = [
            round(abs(obj.dimensions.x) * 1000),
            round(abs(obj.dimensions.y) * 1000),
            round(abs(obj.dimensions.z) * 1000)
        ]
        dims.sort()
        return [dims[1], dims[2], dims[0]], 1
        
    mirror_count = 1
    array_count = 1
    
    # Проверяем модификаторы
    mirror_mod = None
    for mod in obj.modifiers:
        if mod.type == 'MIRROR':
            mirror_mod = mod
            if any(mod.use_axis):
                mirror_count = 2
        elif mod.type == 'ARRAY':
            array_count *= mod.count
    
    if mirror_mod:
        # Сохраняем текущее состояние
        was_visible = mirror_mod.show_viewport
        # Выключаем модификатор
        mirror_mod.show_viewport = False
        # Обновляем сцену
        bpy.context.view_layer.update()
        
        # Получаем размеры без модификатора
        dims = [
            round(abs(obj.dimensions.x) * 1000),
            round(abs(obj.dimensions.y) * 1000),
            round(abs(obj.dimensions.z) * 1000)
        ]
        
        # Возвращаем модификатор в исходное состояние
        mirror_mod.show_viewport = was_visible
        bpy.context.view_layer.update()
    else:
        # Если нет mirror модификатора, просто берем размеры
        dims = [
            round(abs(obj.dimensions.x) * 1000),
            round(abs(obj.dimensions.y) * 1000),
            round(abs(obj.dimensions.z) * 1000)
        ]
    
    # Сортируем размеры
    dims.sort()
    thickness = dims[0]  # Самый маленький размер
    other_dims = sorted(dims[1:], reverse=True)  # Остальные размеры
    
    dims_list = [other_dims[0], other_dims[1], thickness]
    return dims_list, mirror_count * array_count

def analyze_furniture_parts(length_groups=None, excluded_groups=None):
    if length_groups is None:
        length_groups = ['legs']
    if excluded_groups is None:
        excluded_groups = ['fitting']
    
    groups = {}
    total_area = 0
    
    mesh_objects = [obj for obj in bpy.data.objects if obj.type == 'MESH']
    
    for obj in mesh_objects:
        base_name = get_base_name(obj.name)
        dims_list, copies = get_dimensions_and_copies(obj)
        
        if base_name not in groups:
            groups[base_name] = {
                'parts': [],
                'area': 0
            }
            if base_name in length_groups:
                groups[base_name]['length'] = 0
        
        # Добавляем размеры нужное количество раз
        for _ in range(copies):
            groups[base_name]['parts'].append(dims_list)
        
        if base_name in length_groups:
            length = dims_list[0] / 1000 * copies  # высота
            groups[base_name]['length'] = round(groups[base_name]['length'] + length, 2)
        
        if base_name not in excluded_groups:
            # Площадь считаем как высота * глубина
            area = (dims_list[0] / 1000) * (dims_list[1] / 1000) * copies
            groups[base_name]['area'] = round(groups[base_name]['area'] + area, 5)
            total_area += area
    
    groups['total_area'] = round(total_area, 5)
    return groups

def save_dimensions_to_file(filepath, length_groups=None, excluded_groups=None):
    data = analyze_furniture_parts(length_groups, excluded_groups)
    
    # Сортируем части в каждой группе
    for group in data:
        if isinstance(data[group], dict) and 'parts' in data[group]:
            data[group]['parts'].sort(reverse=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

# save_dimensions_to_file(
#     "/Users/rostislavnikolaiev/Desktop/work/dreamers/render_server/blender/dimensions.json",
#     length_groups=['legs'],
#     excluded_groups=['fitting']
# )

# Пример использования:
save_dimensions_to_file(
     "/Users/rostislavnikolaiev/Desktop/work/dreamers/render_server/blender/dimensions.json",
     length_groups=['legs'],
     excluded_groups=['fitting']
)

