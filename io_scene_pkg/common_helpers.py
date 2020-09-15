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
        
def get_raw_object_name(meshname):
    return meshname.upper().replace("_VL", "").replace("_L", "").replace("_M", "").replace("_H", "")


def is_matrix_object(obj):
    obj_name = get_raw_object_name(obj.name)
    return (obj_name == "AXLE0" or obj_name == "AXLE1" or obj_name == "SHOCK0" or obj_name == "SHOCK1" or
            obj_name == "SHOCK2" or obj_name == "SHOCK3" or obj_name == "DRIVER" or obj_name == "ARM0" or
            obj_name == "ARM1" or obj_name == "ARM2" or obj_name == "ARM3" or obj_name == "SHAFT2" or
            obj_name == "SHAFT3" or obj_name == "ENGINE")
