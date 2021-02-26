# ##### BEGIN LICENSE BLOCK #####
#
# This program is licensed under Creative Commons BY-NC-SA:
# https://creativecommons.org/licenses/by-nc-sa/3.0/
#
# Created by Dummiesman, 2016-2020
#
# ##### END LICENSE BLOCK #####

import bpy
import os, struct
import os.path as path

from io_scene_pkg.tex_file import TEXFile

def make_placeholder_texture(name):
    ptw = 2
    pth = 2
    
    im = bpy.data.images.new(name=name, width=ptw, height=pth)
    pixels = list(im.pixels)
    
    for y in range(pth):
        for x in range(ptw):
            is_magenta = x == y
            pixel_color = (1, 0, 1, 1) if is_magenta else (0, 0, 0, 1)
            b_pixel_index = 4 * ((y * ptw) + x)
            
            pixels[b_pixel_index] = pixel_color[0]
            pixels[b_pixel_index+1] = pixel_color[1]
            pixels[b_pixel_index+2] = pixel_color[2]
            pixels[b_pixel_index+3] = pixel_color[3]

    im.pixels = pixels[:]
    im.update()
    return im
    
def find_file_with_game_fallback(file, search_path, subfolder = None, ignore_subdir_on_search_path = False):
    # first search the search_path
    find_path = (path.abspath(path.join(search_path, file))
                 if (subfolder is None or ignore_subdir_on_search_path)
                 else path.abspath(path.join(search_path, subfolder, file)))
    
    #print("find_path initial:" + find_path)
    if path.isfile(find_path):
        return find_path
    
    # then search game dir
    preferences = bpy.context.preferences
    addon_prefs = preferences.addons[__package__].preferences
    if addon_prefs.use_gamepath:
        find_path = (path.abspath(path.join(addon_prefs.gamepath, subfolder, file)) 
                     if subfolder is not None 
                     else path.abspath(path.join(addon_prefs.gamepath, file)))
        #print("find_path game:" + find_path)
        if path.isfile(find_path):
            return find_path

    # wasn't found in game dir or search_path
    return None


def load_texture_from_path(file_path, use_placeholder_if_missing=True):
    # extract the filename for manual image format names
    imgname=path.basename(file_path)
    imgname=os.path.splitext(imgname)[0]
    
    if not path.isfile(file_path):
        return make_placeholder_texture(imgname)
    
    if file_path.lower().endswith(".tex"):
        tf = TEXFile(file_path)
        if tf.is_valid():
            tf_img = tf.to_blender_image(imgname)
            tf_img.filepath_raw = file_path # set filepath manually for TEX stuff, since we make it ourself
            return tf_img
        else:
            print("Invalid TEX file: " + file_path)
    else:
        img = bpy.data.images.load(file_path)
        return img
        
    return None    

    
def try_load_texture(tex_name, search_path):
    existing_image = bpy.data.images.get(tex_name)
    if existing_image is not None:
        return existing_image
    
    find_file = tex_name + ".tex"
    found_file = find_file_with_game_fallback(find_file, search_path, "texture")
    if found_file is not None:
        tf_img = load_texture_from_path(found_file)
        if tf_img is not None:
            return tf_img
    
    standard_extensions = (".tga", ".bmp", ".png")
    for ext in standard_extensions:
        find_file = tex_name + ext
        found_file = find_file_with_game_fallback(find_file, search_path, "texture")
        if found_file is not None:
            return load_texture_from_path(found_file)
        
    return None
 
 
def get_raw_object_name(meshname):
    return meshname.upper().replace("_VL", "").replace("_L", "").replace("_M", "").replace("_H", "")


def get_object_lod_name(item):
    item_upper = item.upper()
    if item_upper.endswith("_H"):
        return "H"
    elif item_upper.endswith("_M"):
        return "M"
    elif item_upper.endswith("_L"):
        return "L"
    elif item_upper.endswith("_VL"):
        return "VL"
    elif item_upper == 'H' or item_upper == 'M' or item_upper == 'L' or item_upper == 'VL':
        return item_upper
    return None


def get_alphabetical_lod_id(item):
    if item == 'H':
        return "A"
    elif item == 'M':
        return "B"
    elif item == 'L':
        return "C"
    elif item == 'VL':
        return "D"
    return "E"


def get_undupe_name(name):
    nidx = name.find('.')
    return name[:nidx] if nidx != -1 else name


def is_matrix_object(obj):
    obj_name = get_raw_object_name(obj.name)
    return (obj_name == "AXLE0" or obj_name == "AXLE1" or obj_name == "SHOCK0" or obj_name == "SHOCK1" or
            obj_name == "SHOCK2" or obj_name == "SHOCK3" or obj_name == "DRIVER" or obj_name == "ARM0" or
            obj_name == "ARM1" or obj_name == "ARM2" or obj_name == "ARM3" or obj_name == "SHAFT2" or
            obj_name == "SHAFT3" or obj_name == "ENGINE")

def convert_vecspace_to_blender(vtx):
    return (vtx[0] * -1, vtx[2], vtx[1])
    
def convert_vecspace_to_mm2(vtx):
    return (vtx[0] * -1, vtx[2], vtx[1])