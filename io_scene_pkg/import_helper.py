# ##### BEGIN LICENSE BLOCK #####
#
# This program is licensed under Creative Commons BY-NC-SA:
# https://creativecommons.org/licenses/by-nc-sa/3.0/
#
# Copyright (C) Dummiesman, 2016
#
# ##### END LICENSE BLOCK #####
import bpy, mathutils
import os, struct
import os.path as path

import io_scene_pkg.binary_helper as bin

def get_raw_object_name(meshname):
    return meshname.upper().replace("_VL", "").replace("_L", "").replace("_M", "").replace("_H", "")

def find_matrix(meshname, object, pkg_path):
    """search for *.mtx and load if found"""
    mesh_name_parsed = get_raw_object_name(meshname)
    find_path = pkg_path[:-4] + '_' + mesh_name_parsed + ".mtx"
    if path.isfile(find_path):
        mtxfile = open(find_path, 'rb')
        mtx_info = struct.unpack('ffffffffffff', mtxfile.read(48))
        # 6 7 8 = COG, 9 10 11 = ORIGIN
        object.location = (mtx_info[9], mtx_info[11] * -1, mtx_info[10])
    return
    
def try_load_texture(tex_name, pkg_path):
    """look for tga, bmp, or png texture, and load if found"""
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
    
def check_degenerate(i1, i2, i3):
    if i1 == i2 or i1 == i3 or i2 == i3:
        return True
    return False
    
def triangle_strip_to_list(strip, clockwise):
    """convert a strip of triangles into a list of triangles"""
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
    
def convert_triangle_strips(tristrip_data):
    """convert Midnight Club triangle strips into triangle list data"""
    last_strip_cw = False
    last_strip_indices = []
    trilist_data = []
    for us in tristrip_data:
        # flags
        FLAG_CW = ((us & (1 << 14)) != 0)
        FLAG_END = ((us & (1 << 15)) != 0)
        INDEX = us
        if FLAG_CW:
            INDEX &= ~(1 << 14)
        if FLAG_END:
            INDEX &= ~(1 << 15)
        # cw flag is only set at the first index in the strip
        if len(last_strip_indices) == 0:
            last_strip_cw = FLAG_CW
        last_strip_indices.append(INDEX)
        # are we done with this strip?
        if FLAG_END:
            trilist_data.extend(triangle_strip_to_list(last_strip_indices, last_strip_cw))
            last_strip_indices = []
    
    return trilist_data

def read_vertex_data(file, FVF_FLAGS, compressed):
    """read PKG vertex data into a tuple"""
    vnorm = mathutils.Vector((1, 1, 1))
    vuv = (0, 0)
    vcolor = mathutils.Color((1, 1, 1))
    if FVF_FLAGS.has_flag("D3DFVF_NORMAL"):
        if compressed:
          vnorm = bin.read_cfloat3(file)
        else:
          vnorm = bin.read_float3(file)
    if FVF_FLAGS.has_flag("D3DFVF_DIFFUSE"):
        c4d = bin.read_color4d(file)
        vcolor = mathutils.Color((c4d[0], c4d[1], c4d[2]))
    if FVF_FLAGS.has_flag("D3DFVF_SPECULAR"):
        c4d = bin.read_color4d(file)
        vcolor = mathutils.Color((c4d[0], c4d[1], c4d[2]))
    if FVF_FLAGS.has_flag("D3DFVF_TEX1"):
        if compressed:
          vuv = bin.read_cfloat2(file)
        else:
          vuv = bin.read_float2(file)
          
    return (vnorm, vuv, vcolor)