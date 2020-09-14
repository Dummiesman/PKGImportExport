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
      
from io_scene_pkg.tex_file import TEXFile
                       
#######################
### Other Functions ###
#######################

def get_object_name_without_lod_suffix(meshname):
    """Strips off all suffixes for LOD"""
    return meshname.upper().replace("_VL", "").replace("_L", "").replace("_M", "").replace("_H", "")

def find_matrix(meshname, object, pkg_path):
    """search for *.mtx and load if found"""
    mesh_name_parsed = get_object_name_without_lod_suffix(meshname)
    find_path = pkg_path[:-4] + '_' + mesh_name_parsed + ".mtx"
    
    if path.isfile(find_path):
        mtxfile = open(find_path, 'rb')
        mtx_info = struct.unpack('ffffffffffff', mtxfile.read(48))
        
        mtx_min = (mtx_info[0], mtx_info[2] * -1, mtx_info[1])
        mtx_max = (mtx_info[3], mtx_info[5] * -1, mtx_info[4])
        pivot =  (mtx_info[6], mtx_info[8] * -1, mtx_info[7])
        origin = (mtx_info[9], mtx_info[11] * -1, mtx_info[10])
       
        return (True, mtx_min, mtx_max, pivot, origin)
    return (False, None, None, None, None)
    
def __try_load_texture(tex_name, search_path):
    """look for tex, tga, bmp, or png texture, and load if found"""
    texturepath = path.abspath(path.join(search_path, "texture\\" + tex_name))
    find_path = texturepath + ".tex"
    if os.path.isfile(find_path):
        tf = TEXFile(find_path)
        tf_img = tf.to_blender_image(tex_name)
        return tf_img
    find_path = texturepath + ".tga"
    if os.path.isfile(find_path):
        img = bpy.data.images.load(find_path)
        return img
    find_path = texturepath + ".bmp"
    if os.path.isfile(find_path):
        img = bpy.data.images.load(find_path)
        return img
    find_path = texturepath + ".png"
    if os.path.isfile(find_path):
        img = bpy.data.images.load(find_path)
        return img
    return None
    
def try_load_texture(context, tex_name, path):
    existing_image = bpy.data.images.get(tex_name)
    if existing_image is not None:
        return existing_image
        
    # try to load with the initial path
    tex = __try_load_texture(tex_name, path)
    if tex is not None:
        return tex
        
    # fallback to game path if applicable!
    if context is None:
        return None
        
    preferences = context.preferences
    addon_prefs = preferences.addons[__package__].preferences
    
    if addon_prefs.use_gamepath:
        tex = __try_load_texture(tex_name, addon_prefs.gamepath)
    return tex
        
    

def check_degenerate(i1, i2, i3):
    if i1 == i2 or i1 == i3 or i2 == i3:
        return True
    return False
    
def triangle_strip_to_list(strip, clockwise):
    """convert a strip of triangles into a list of triangles"""
    triangle_list = []
    for v in range(len(strip) - 2):
        if clockwise:
            triangle_list.extend([strip[v+1], strip[v], strip[v+2]])
        else:
            triangle_list.extend([strip[v], strip[v+1], strip[v+2]])
            
        # make sure we aren't resetting the clockwise
        # flag if we have a degenerate triangle
        if not check_degenerate(strip[v], strip[v+1], strip[v+2]):
            clockwise = not clockwise

    return triangle_list
    
def convert_triangle_strips(tristrip_data):
    """convert Midnight Club triangle strips into triangle list data"""
    last_strip_cw = False
    last_strip_indices = []
    trilist_data = []
    for us in tristrip_data:
        # flags processing
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
            last_strip_cw = False
            last_strip_indices = []
    
    return trilist_data

def read_vertex_data(file, FVF_FLAGS, compressed):
    """read PKG vertex data into a tuple"""
    vnorm = mathutils.Vector((1, 1, 1))
    vuv = (0, 0)
    vcolor = mathutils.Color((1, 1, 1))
    if FVF_FLAGS.has_flag("D3DFVF_NORMAL"):
        vnorm = bin.read_cfloat3(file) if compressed else bin.read_float3(file)
    if FVF_FLAGS.has_flag("D3DFVF_DIFFUSE"):
        c4d = bin.read_color4d(file)
        vcolor = mathutils.Color((c4d[0], c4d[1], c4d[2]))
    if FVF_FLAGS.has_flag("D3DFVF_SPECULAR"):
        c4d = bin.read_color4d(file)
        vcolor = mathutils.Color((c4d[0], c4d[1], c4d[2]))
    if FVF_FLAGS.has_flag("D3DFVF_TEX1"):
        vuv = bin.read_cfloat2(file) if compressed else bin.read_float2(file)
          
    return (vnorm, vuv, vcolor)

def populate_material(context, mtl, shader, pkg_path):
    """ Initializes a material """
    # get tex name
    texture_name = "age:notexture" if shader.name is None else shader.name
    
    # basics
    mtl.use_nodes = True
    mtl.use_backface_culling = True
    
    # setup colors
    bsdf = mtl.node_tree.nodes["Principled BSDF"]
    bsdf.inputs['Base Color'].default_value = shader.diffuse_color
    bsdf.inputs['Emission'].default_value = shader.emissive_color
    bsdf.inputs['Specular'].default_value = shader.shininess
    bsdf.inputs['Roughness'].default_value = 0

    mtl.diffuse_color = shader.diffuse_color
    mtl.specular_intensity = 0.1
    mtl.metallic = shader.shininess

    # alpha vars
    mtl_alpha = shader.diffuse_color[3]
    tex_depth = 0
        
    # look for a texture
    tex_result = None
    tex_image_node = None
    if shader.name is not None:
        tex_result = try_load_texture(context, texture_name, path.join(os.path.dirname(pkg_path), "../"))
    
    if tex_result is not None:
        tex_depth = tex_result.depth
        tex_image_node = mtl.node_tree.nodes.new('ShaderNodeTexImage')
        tex_image_node.image = tex_result
        tex_image_node.location = mathutils.Vector((-640.0, 20.0))
        
        blend_node = mtl.node_tree.nodes.new('ShaderNodeMixRGB')
        blend_node.inputs['Color2'].default_value = shader.diffuse_color
        blend_node.inputs['Fac'].default_value = 1.0
        blend_node.blend_type = 'MULTIPLY'
        blend_node.label = "Diffuse Color"
        blend_node.location = mathutils.Vector((-260.0, 160.0))
        
        mtl.node_tree.links.new(blend_node.inputs['Color1'], tex_image_node.outputs['Color'])
        mtl.node_tree.links.new(bsdf.inputs['Base Color'], blend_node.outputs['Color'])

    # setup emission
    if tex_image_node is not None:
        blend_node = mtl.node_tree.nodes.new('ShaderNodeMixRGB')
        blend_node.inputs['Color2'].default_value = shader.emissive_color
        blend_node.inputs['Fac'].default_value = 1.0
        blend_node.blend_type = 'MULTIPLY'
        blend_node.label = "Emission Color"
        blend_node.location = mathutils.Vector((-260.0, -20.0))
        
        mtl.node_tree.links.new(blend_node.inputs['Color1'], tex_image_node.outputs['Color'])
        mtl.node_tree.links.new(bsdf.inputs['Emission'], blend_node.outputs['Color'])
     
    # have alpha?
    if mtl_alpha < 1 or tex_depth == 32:
        mtl.blend_method = 'BLEND'
        
    # assign transparent channel on BSDF
    if tex_image_node is not None:
        blend_node = mtl.node_tree.nodes.new('ShaderNodeMath')
        blend_node.inputs[0].default_value = mtl_alpha
        blend_node.inputs[1].default_value = 1.0
        blend_node.operation = 'MULTIPLY'
        blend_node.label = "Alpha"
        blend_node.location = mathutils.Vector((-260.0, -200.0))
        
        mtl.node_tree.links.new(blend_node.inputs[1], tex_image_node.outputs['Alpha'])
        mtl.node_tree.links.new(bsdf.inputs['Alpha'], blend_node.outputs[0])
        
    mtl.name = texture_name

        