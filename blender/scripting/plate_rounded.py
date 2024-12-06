import bpy
import bmesh
from math import radians
import math


def create_rounded_plate(length=2168, width=468, thickness=16, corner_radius=44, corner_segments=30):
    # Удаляем предыдущий меш с таким именем, если он существует
    if "Rounded_Plate" in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects["Rounded_Plate"], do_unlink=True)

    # Создаем новый меш и объект
    mesh = bpy.data.meshes.new("Rounded_Plate")
    obj = bpy.data.objects.new("Rounded_Plate", mesh)

    # Привязываем объект к сцене
    scene = bpy.context.scene
    scene.collection.objects.link(obj)

    # Создаем bmesh для построения геометрии
    bm = bmesh.new()

    # Конвертируем размеры из миллиметров в метры
    length = length / 1000
    width = width / 1000
    thickness = thickness / 1000
    corner_radius = corner_radius / 1000

    # Создаем вершины для верхней грани
    top_verts = []
    bottom_verts = []
    x = length / 2 - corner_radius
    y = width / 2 - corner_radius

    # Создаем угловые дуги
    for corner in range(4):
        angle_start = radians(90 * corner)
        for i in range(corner_segments):
            angle = angle_start + radians(90) * i / (corner_segments - 1)
            px = math.cos(angle) * corner_radius
            py = math.sin(angle) * corner_radius

            # Координаты для верхней и нижней вершины
            if corner == 0:
                pos = (x + px, y + py)
            elif corner == 1:
                pos = (-x + px, y + py)
            elif corner == 2:
                pos = (-x + px, -y + py)
            else:
                pos = (x + px, -y + py)

            # Добавляем верхнюю и нижнюю вершину
            top_verts.append(bm.verts.new((pos[0], pos[1], thickness / 2)))
            bottom_verts.append(bm.verts.new((pos[0], pos[1], -thickness / 2)))

    # Создаем верхнюю и нижнюю грани
    bm.faces.new(top_verts)
    bm.faces.new(bottom_verts[::-1])  # Обратный порядок для правильной нормали

    # Создаем боковые грани
    n_verts = len(top_verts)
    for i in range(n_verts):
        next_i = (i + 1) % n_verts
        verts = [
            top_verts[i],
            top_verts[next_i],
            bottom_verts[next_i],
            bottom_verts[i]
        ]
        bm.faces.new(verts)

    # Обновляем меш
    bm.to_mesh(mesh)
    bm.free()

    # Поворачиваем на 90 градусов по X
    obj.rotation_euler.z = radians(90)

    # Применяем поворот и масштаб
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    # Применяем трансформации
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

    # Снимаем выделение
    obj.select_set(False)

    return obj


# Создаем плиту с заданными параметрами
plate = create_rounded_plate()