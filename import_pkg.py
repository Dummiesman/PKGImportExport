# ##### BEGIN LICENSE BLOCK #####
#
# This program is licensed under Creative Commons Attribution-NonCommercial-ShareAlike 3.0
# https://creativecommons.org/licenses/by-nc-sa/3.0/
#
# Copyright (C) Dummiesman, 2016
#
# ##### END LICENSE BLOCK #####

import os
import time
import struct

import bpy
import bmesh
import mathutils
from mathutils import*
import os.path as path
from math import radians

global scn
scn = None

global pkg_path
pkg_path = None

######################################################
# IMPORT HELPERS
######################################################

def read_angel_string(file):
    str_len = struct.unpack('B',file.read(1))[0]
    if str_len == 0:
        return ''
    else:
        return_string = file.read(str_len - 1).decode("utf-8")
        file.seek(1,1)
        return return_string

def get_raw_object_name(meshname):
    return meshname.replace("_VL","").replace("_L","").replace("_M","").replace("_H","")

def find_matrix(meshname,object):
    mesh_name_parsed = get_raw_object_name(meshname)
    find_path = pkg_path[:-4] + '_' + mesh_name_parsed + ".mtx"
    if os.path.isfile(find_path):
        mtxfile = open(find_path, 'rb')
        mtx_info = struct.unpack('ffffffffffff',mtxfile.read(48))
        # 6 7 8 = COG, 9 10 11 = ORIGIN
        object.location = (mtx_info[9],mtx_info[11] * -1,mtx_info[10])
    return

def read_float(file):
    return struct.unpack('f',file.read(4))[0]

def read_float3(file):
    return struct.unpack('fff',file.read(12))

def read_float2(file):
    return struct.unpack('ff',file.read(8))

def read_color4f(file):
    return struct.unpack('ffff',file.read(16))

def read_color4d(file):
    c4d = struct.unpack('BBBB',file.read(4))
    return [c4d[0]/255,c4d[1]/255,c4d[2]/255,c4d[3]/255]

######################################################
# IMPORT MAIN FILES
######################################################
def try_load_texture(tex_name):
    texturepath = path.abspath(path.join(os.path.dirname(pkg_path) ,"../texture//" + tex_name))
    find_path = texturepath + ".tga"
    if os.path.isfile(find_path):
        #prioritize TGA
        img = bpy.data.images.load(find_path)
        #black == alpha? o.O
        img.use_alpha = False
        return img
    find_path = texturepath + ".bmp"
    if os.path.isfile(find_path):
        img = bpy.data.images.load(find_path)
        return img
    return False
    
def read_shaders_file(file,length,offset):
    shadertype_raw, shaders_per_paintjob = struct.unpack('2L',file.read(8))
    shader_type = "float"
    num_paintjobs = shadertype_raw
    #determine real shader type
    if shadertype_raw > 128:
        #byte shader. also we need to do some math
        num_paintjobs -= 128
        shader_type = "byte"
    
    #debug
    print('\tloading ' + str(shaders_per_paintjob) + ' shaders')
    
    for num in range(shaders_per_paintjob):
        #read in only ONE set of shaders. No need for more
        texture_name = read_angel_string(file)
        if texture_name == '':
            #matte material
            texture_name = "mm2:notexture"
        #print('Found shader (' + str(num) + '): ' + texture_name)
        #initialize these
        diffuse_color = None
        ambient_color = None
        specular_color = None
        reflective_color = None
        if shader_type == "float":
            ambient_color = read_color4f(file)
            diffuse_color = read_color4f(file)
            specular_color = read_color4f(file)
            reflective_color = read_color4f(file)
        elif shader_type == "byte":
            ambient_color = read_color4d(file)
            diffuse_color = read_color4d(file)
            specular_color = read_color4d(file)
        shininess = read_float(file)
        
        #insert this data
        mtl = bpy.data.materials.get(str(num))
        if mtl != None:
            mtl.diffuse_color = (diffuse_color[0],diffuse_color[1],diffuse_color[2])
            mtl.specular_color = (specular_color[0],specular_color[1],specular_color[2])
            mtl.translucency = diffuse_color[3] - 1
            mtl.raytrace_mirror.reflect_factor = shininess
            #look for a texture
            tex_result = try_load_texture(texture_name)
            if  tex_result != False:
                mtex = mtl.texture_slots.add()
                cTex = bpy.data.textures.new(texture_name, type = 'IMAGE')
                cTex.image = tex_result
                mtex.texture = cTex
            mtl.name = texture_name
     
    #skip to the end of this FILE
    file.seek(length - (file.tell() - offset),1)
    return

def read_xrefs(file):
    scn = bpy.context.scene
    #read xrefs
    num_xrefs = struct.unpack('L',file.read(4))[0]
    for num in range(num_xrefs):
        #skip matrix for now :(
        file.seek(36,1)
        #get position
        xref_position = read_float3(file)
        xref_name = file.read(32).decode("utf-8")
        ob = bpy.data.objects.new("xref:" + xref_name, None)
        ob.location = (xref_position[0],xref_position[2] * -1,xref_position[1])
        ob.show_name = True
        ob.show_axis = True
        scn.objects.link(ob)
    
def read_geometry_file(file,meshname):
    scn = bpy.context.scene
    #ADD THE MESH AND LINK IT TO THE SCENE
    me = bpy.data.meshes.new(meshname+'Mesh')
    ob = bpy.data.objects.new(meshname, me)
    
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    uv_layer = bm.loops.layers.uv.new()
    tex_layer = bm.faces.layers.tex.new()

    scn.objects.link(ob)
    scn.objects.active = ob
    
    bpy.ops.object.mode_set(mode='EDIT', toggle=False)
    #THERE :) Now read file data
    num_sections, num_vertices_tot, num_indices_tot, num_sections_dupe, fvf = struct.unpack('5L',file.read(20))
   
    #mesh data holders
    current_vert_offset = 0
    uvs = []     
    ob_current_material = -1    
    for num in range(num_sections):
        num_strips, strip_flags, shader_offset = struct.unpack('HHL',file.read(8))
        #FVF stuff
        FVF_NORMALS = ((fvf & 16) != 0)
        #do we have this material?
        if bpy.data.materials.get(str(shader_offset)) is None:
            #we must make it
            bpy.data.materials.new(name=str(shader_offset))
        ob.data.materials.append(bpy.data.materials.get(str(shader_offset)))
        ob_current_material += 1
        for num2 in range(num_strips):
            #primtype
            file.seek(4,1)
            num_vertices = struct.unpack('L',file.read(4))[0]
            # READ VERTICES HERE
            for i in range(num_vertices):
                vpos = read_float3(file)
                vnorm = mathutils.Vector((1,1,1))
                if FVF_NORMALS:
                    vnorm = read_float3(file)
                vuv = read_float2(file)
                vtx = bm.verts.new((vpos[0],vpos[2] * -1,vpos[1]))
                vtx.normal = mathutils.Vector((vnorm[0],vnorm[2] * -1,vnorm[1]))
                uvs.append((vuv[0],(vuv[1] * -1) + 1))
            ###
            bm.verts.ensure_lookup_table()
            num_indices = struct.unpack('L',file.read(4))[0]
            for i in range(int(num_indices/3)):
                face_data = struct.unpack('3H',file.read(6))
                i1 = face_data[0] + current_vert_offset
                i2 = face_data[1] + current_vert_offset
                i3 = face_data[2] + current_vert_offset
                try:
                    face = bm.faces.new((bm.verts[i1], bm.verts[i2], bm.verts[i3]))
                    face.smooth = True
                    face.material_index = ob_current_material 
                    face.loops[0][uv_layer].uv = uvs[i1]
                    face.loops[1][uv_layer].uv = uvs[i2]
                    face.loops[2][uv_layer].uv = uvs[i3]
                except:
                    print ('PKG add face error :(')
            
            current_vert_offset += num_vertices
    
    #bm.normal_update()
    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    bm.to_mesh(me)
    bm.free()
    #lastly, look for a MTX file
    find_matrix(meshname,ob)
    return
 
######################################################
# IMPORT
######################################################

def load_pkg(filepath,
             context):
    global SCN
    global pkg_path
    pkg_path = filepath
    
    print("importing PKG: %r..." % (filepath))

    if bpy.ops.object.select_all.poll():
        bpy.ops.object.select_all(action='DESELECT')

    time1 = time.clock()

    file = open(filepath, 'rb')
    pkg_size = os.path.getsize(filepath)

    scn = context.scene
    SCN = scn
    
    #PKG STUF
    PKGTYPE = file.read(4).decode("utf-8")
    if PKGTYPE != "PKG3":
        print('\tFatal Error:  PKG file is wrong format : ' + PKGTYPE)
        file.close()
        return
    
    ###READ PKG FILE DATA###
    while file.tell() !=  pkg_size:
        file_header = file.read(4).decode("utf-8")
        
        #check header
        if file_header != "FILE":
            print('\tFatal Error: PKG file is corrupt, missing FILE header at ' + str(file.tell()))
            file.close()
            return
            
        #found a proper FILE header
        file_name = read_angel_string(file)
        file_length = struct.unpack('L',file.read(4))[0]
        print('\t[' + str(round(time.clock() - time1,3)) + '] processing : ' + file_name)
        if file_name == "shaders":
            #load shaders file
            read_shaders_file(file,file_length,file.tell())
            #file.seek(file_length,1)
        elif file_name == "offset":
            #skip over this LEL
            file.seek(file_length,1)
        elif file_name == "xrefs":
            read_xrefs(file)
        else:
            #assume geometry
            read_geometry_file(file,file_name)
    ###END READ PKG FILE DATA###


    print(" done in %.4f sec." % (time.clock() - time1))
    file.close()


def load(operator,
         context,
         filepath="",
         ):

    load_pkg(filepath,
             context,
             )

    return {'FINISHED'}
