# ##### BEGIN LICENSE BLOCK #####
#
# This program is licensed under Creative Commons BY-NC-SA:
# https://creativecommons.org/licenses/by-nc-sa/3.0/
#
# Copyright (C) Dummiesman, 2016
#
# ##### END LICENSE BLOCK #####
import bpy
import os, struct
import os.path as path

def get_raw_object_name(meshname):
    return meshname.upper().replace("_VL", "").replace("_L", "").replace("_M", "").replace("_H", "")

def find_matrix(meshname, object, pkg_path):
    mesh_name_parsed = get_raw_object_name(meshname)
    find_path = pkg_path[:-4] + '_' + mesh_name_parsed + ".mtx"
    if path.isfile(find_path):
        mtxfile = open(find_path, 'rb')
        mtx_info = struct.unpack('ffffffffffff', mtxfile.read(48))
        # 6 7 8 = COG, 9 10 11 = ORIGIN
        object.location = (mtx_info[9], mtx_info[11] * -1, mtx_info[10])
    return
    
def try_load_texture(tex_name, pkg_path):
    texturepath = path.abspath(path.join(os.path.dirname(pkg_path), "../texture//" + tex_name))
    find_path = texturepath + ".tga"
    if os.path.isfile(find_path):
        # prioritize TGA
        img = bpy.data.images.load(find_path)
        # black == alpha? o.O
        img.use_alpha = False
        return img
    find_path = texturepath + ".bmp"
    if os.path.isfile(find_path):
        img = bpy.data.images.load(find_path)
        return img
    find_path = texturepath + ".png"
    if os.path.isfile(find_path):
        img = bpy.data.images.load(find_path)
        return img
    return False
    
def triangle_strip_to_list(strip, clockwise):
    triangle_list = []
    for v in range(2, len(strip)):
        if clockwise:
            triangle_list.extend([strip[v-2], strip[v], strip[v-1]])
        else:
            triangle_list.extend([strip[v], strip[v-2], strip[v-1]])
        # make sure we aren't resetting the clockwise
        # flag if we have a degenerate triangle
        if not check_degenerate(strip[v], strip[v-1], strip[v-2]):
            clockwise = not clockwise

    return triangle_list