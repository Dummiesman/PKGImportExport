# ##### BEGIN LICENSE BLOCK #####
#
# This program is licensed under Creative Commons BY-NC-SA:
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
    str_len = struct.unpack('B', file.read(1))[0]
    if str_len == 0:
        return ''
    else:
        return_string = file.read(str_len - 1).decode("utf-8")
        file.seek(1, 1)
        return return_string


def get_raw_object_name(meshname):
    return meshname.replace("_VL", "").replace("_L", "").replace("_M", "").replace("_H", "")


def find_matrix(meshname, object):
    mesh_name_parsed = get_raw_object_name(meshname)
    find_path = pkg_path[:-4] + '_' + mesh_name_parsed + ".mtx"
    if os.path.isfile(find_path):
        mtxfile = open(find_path, 'rb')
        mtx_info = struct.unpack('ffffffffffff', mtxfile.read(48))
        # 6 7 8 = COG, 9 10 11 = ORIGIN
        object.location = (mtx_info[9], mtx_info[11] * -1, mtx_info[10])
    return


def read_float(file):
    return struct.unpack('f', file.read(4))[0]


def read_float3(file):
    return struct.unpack('fff', file.read(12))


def read_cfloat3(file):
    btc = struct.unpack('bbb', file.read(3))
    return btc[0]/128, btc[1]/128, btc[2]/128


def read_cfloat2(file):
    stc = struct.unpack('HH', file.read(4))
    return (stc[0]/128) - 128, (stc[1]/128) - 128


def read_float2(file):
    return struct.unpack('ff', file.read(8))


def read_color4f(file):
    return struct.unpack('ffff', file.read(16))


def read_color4d(file):
    c4d = struct.unpack('BBBB', file.read(4))
    return [c4d[0]/255, c4d[1]/255, c4d[2]/255, c4d[3]/255]

lastob = ""
    
def triangle_strip_to_list(strip,clockwise):
    triangle_list = []
    for v in range(2,len(strip)):
        if clockwise:
            triangle_list.extend([strip[v-2], strip[v], strip[v-1]])
        else:
            triangle_list.extend([strip[v], strip[v-2], strip[v-1]])
        clockwise = not clockwise
    return triangle_list

######################################################
# IMPORT MAIN FILES
######################################################
def try_load_texture(tex_name):
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
    return False


def read_shaders_file(file, length, offset):
    shadertype_raw, shaders_per_paintjob = struct.unpack('2L', file.read(8))
    shader_type = "float"
    num_paintjobs = shadertype_raw
    # determine real shader type
    if shadertype_raw > 128:
        # byte shader. also we need to do some math
        num_paintjobs -= 128
        shader_type = "byte"

    # debug
    print('\tloading ' + str(shaders_per_paintjob) + ' shaders')

    for num in range(shaders_per_paintjob):
        # read in only ONE set of shaders. No need for more
        texture_name = read_angel_string(file)
        if texture_name == '':
            # matte material
            texture_name = "mm2:notexture"
        # initialize these
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

        # insert this data
        mtl = bpy.data.materials.get(str(num))
        if mtl is not None:
            mtl.diffuse_color = (diffuse_color[0], diffuse_color[1], diffuse_color[2])
            mtl.specular_color = (specular_color[0], specular_color[1], specular_color[2])
            mtl.raytrace_mirror.reflect_factor = shininess
            mtl_alpha_test = (diffuse_color[3] - 1) * -1
            if mtl_alpha_test > 0:
                mtl.use_transparency = True
                mtl.alpha = mtl_alpha_test
            # look for a texture
            tex_result = try_load_texture(texture_name)
            if tex_result is not False:
                mtex = mtl.texture_slots.add()
                cTex = bpy.data.textures.new(texture_name, type='IMAGE')
                cTex.image = tex_result
                mtex.texture = cTex
            mtl.name = texture_name

    # skip to the end of this FILE
    file.seek(length - (file.tell() - offset), 1)
    return


def read_xrefs(file):
    scn = bpy.context.scene
    # read xrefs
    num_xrefs = struct.unpack('L', file.read(4))[0]
    for num in range(num_xrefs):
        # skip matrix for now :(
        file.seek(36, 1)
        # get position
        xref_position = read_float3(file)
        xref_name = file.read(32).decode("utf-8")
        ob = bpy.data.objects.new("xref:" + xref_name, None)
        ob.location = (xref_position[0], xref_position[2] * -1, xref_position[1])
        ob.show_name = True
        ob.show_axis = True
        scn.objects.link(ob)
       
def read_geometry_file(file, meshname):
    scn = bpy.context.scene
    # ADD THE MESH AND LINK IT TO THE SCENE
    me = bpy.data.meshes.new(meshname+'Mesh')
    ob = bpy.data.objects.new(meshname, me)

    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    uv_layer = bm.loops.layers.uv.new()
    tex_layer = bm.faces.layers.tex.new()
    vc_layer = bm.loops.layers.color.new()
    
    scn.objects.link(ob)
    scn.objects.active = ob
    
    bpy.ops.object.mode_set(mode='EDIT', toggle=False)
    # THERE :) Now read file data
    num_sections, num_vertices_tot, num_indices_tot, num_sections_dupe, fvf = struct.unpack('5L', file.read(20))

    # mesh data holders
    current_vert_offset = 0
    uvs = []
    colors = []
    ob_current_material = -1
    for num in range(num_sections):
        #print("READING SECTION " + str(num))
        num_strips, strip_flags = struct.unpack('HH', file.read(4))
        shader_offset = 0
        #strip flags
        FLAG_compact_strips = ((strip_flags&(1<<8))!=0)
        # print("DEBUG : FLAG_compact_strip == " + str(FLAG_compact_strips)) 
        # fvf flags
        FVF_NORMALS = ((fvf & 16) != 0)
        FVF_UV = ((fvf & 256) != 0)
        FVF_COLOR = ((fvf&(1<<6))!=0)
        if FLAG_compact_strips:
            shader_offset = struct.unpack('H', file.read(2))[0]
        else:
            shader_offset = struct.unpack('L', file.read(4))[0]
        # do we have this material?
        if bpy.data.materials.get(str(shader_offset)) is None:
            # we must make it
            bpy.data.materials.new(name=str(shader_offset))
        ob.data.materials.append(bpy.data.materials.get(str(shader_offset)))
        ob_current_material += 1
        
        if FLAG_compact_strips:
            ############################
            # READ MIDNIGHT CLUB STRIP #
            ############################
            for num2 in range(num_strips):
                # primtype
                file.seek(2, 1)
                num_vertices = struct.unpack('H', file.read(2))[0]
                for i in range(num_vertices):
                    vpos = read_float3(file)
                    vnorm = mathutils.Vector((1,1,1))
                    vuv = (0,0)
                    vcolor = mathutils.Color((1, 1, 1))
                    if FVF_NORMALS:
                        vnorm = read_cfloat3(file)
                    if FVF_COLOR:
                        c4d = read_color4d(file)
                        vcolor = mathutils.Color((c4d[0],c4d[1],c4d[2]))
                    if FVF_UV:
                        vuv = read_cfloat2(file)
                    # add vertex to mesh
                    vtx = bm.verts.new((vpos[0], vpos[2] * -1, vpos[1]))
                    vtx.normal = mathutils.Vector((vnorm[0], vnorm[2] * -1, vnorm[1]))
                    uvs.append((vuv[0], (vuv[1] * -1) + 1))
                    colors.append(vcolor)
                # read indices
                bm.verts.ensure_lookup_table()
                num_indices = struct.unpack('H', file.read(2))[0]
                # read our indices into an array
                tristrip_data = struct.unpack('H' * num_indices, file.read(2 * num_indices))
                #print("tristip_data len = " + str(len(tristrip_data)) + " of " + str(num_indices))
                trilist_data = []
                # convert all our strips
                last_strip_cw = False
                last_strip_indices = []
                for us in tristrip_data:
                    # flags
                    FLAG_CW = ((us&(1<<14))!=0)
                    FLAG_END = ((us&(1<<15))!=0)
                    INDEX = us
                    if FLAG_CW:
                        INDEX = INDEX & ~(1<<14)
                    if FLAG_END:
                        INDEX = INDEX & ~(1<<15)
                    # other stuff
                    last_strip_cw = FLAG_CW
                    last_strip_indices.append(INDEX)
                    # are we done with this?
                    if FLAG_END:
                        trilist_data.extend(triangle_strip_to_list(last_strip_indices,last_strip_cw))
                        last_strip_indices = []
                for i in range(0,len(trilist_data),3):
                    i1 = trilist_data[i] + current_vert_offset
                    i2 = trilist_data[i+1] + current_vert_offset
                    i3 = trilist_data[i+2] + current_vert_offset
                    try:
                        face = bm.faces.new((bm.verts[i1], bm.verts[i2], bm.verts[i3]))
                        face.smooth = True
                        face.material_index = ob_current_material
                        # set uvs
                        face.loops[0][uv_layer].uv = uvs[i1]
                        face.loops[1][uv_layer].uv = uvs[i2]
                        face.loops[2][uv_layer].uv = uvs[i3]
                        # set colors
                        face.loops[0][vc_layer] = colors[i1]
                        face.loops[1][vc_layer] = colors[i2]
                        face.loops[2][vc_layer] = colors[i3]
                    except Exception as e:
                        print ('PKG add face error :(')
                        
                current_vert_offset += num_vertices
        else:
            ##############################
            # READ MIDTOWN MADNESS STRIP #
            ##############################
            for num2 in range(num_strips):
                # primtype
                file.seek(4, 1)
                num_vertices = struct.unpack('L', file.read(4))[0]
                # READ VERTICES HERE
                for i in range(num_vertices):
                    vpos = read_float3(file)
                    vnorm = mathutils.Vector((1, 1, 1))
                    vuv = (0,0)
                    vcolor = mathutils.Color((1, 1, 1))
                    if FVF_NORMALS:
                        vnorm = read_float3(file)
                    if FVF_COLOR:
                        c4d = read_color4d(file)
                        vcolor = mathutils.Color((c4d[0],c4d[1],c4d[2]))
                    if FVF_UV:
                        vuv = read_float2(file)
                    # add vertex to mesh
                    vtx = bm.verts.new((vpos[0], vpos[2] * -1, vpos[1]))
                    vtx.normal = mathutils.Vector((vnorm[0], vnorm[2] * -1, vnorm[1]))
                    uvs.append((vuv[0], (vuv[1] * -1) + 1))
                    colors.append(vcolor)
                # read indices
                bm.verts.ensure_lookup_table()
                num_indices = struct.unpack('L', file.read(4))[0]
                for i in range(int(num_indices/3)):
                    face_data = struct.unpack('3H', file.read(6))
                    i1 = face_data[0] + current_vert_offset
                    i2 = face_data[1] + current_vert_offset
                    i3 = face_data[2] + current_vert_offset
                    try:
                        face = bm.faces.new((bm.verts[i1], bm.verts[i2], bm.verts[i3]))
                        face.smooth = True
                        face.material_index = ob_current_material
                        # set uvs
                        face.loops[0][uv_layer].uv = uvs[i1]
                        face.loops[1][uv_layer].uv = uvs[i2]
                        face.loops[2][uv_layer].uv = uvs[i3]
                        # set colors
                        face.loops[0][vc_layer] = colors[i1]
                        face.loops[1][vc_layer] = colors[i2]
                        face.loops[2][vc_layer] = colors[i3]
                    except Exception as e:
                        print ('PKG add face error :(')
                        print(str(e))

                current_vert_offset += num_vertices

    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    bm.to_mesh(me)
    bm.free()
    # lastly, look for a MTX file
    find_matrix(meshname, ob)
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

    # PKG STUF
    PKGTYPE = file.read(4).decode("utf-8")
    if PKGTYPE != "PKG3":
        print('\tFatal Error:  PKG file is wrong format : ' + PKGTYPE)
        file.close()
        return

    # READ PKG FILE DATA
    while file.tell() != pkg_size:
        file_header = file.read(4).decode("utf-8")

        # check header
        if file_header != "FILE":
            print('\tFatal Error: PKG file is corrupt, missing FILE header at ' + str(file.tell()))
            file.close()
            return

        # found a proper FILE header
        file_name = read_angel_string(file)
        file_length = struct.unpack('L', file.read(4))[0]
        print('\t[' + str(round(time.clock() - time1, 3)) + '] processing : ' + file_name)
        if file_name == "shaders":
            # load shaders file
            read_shaders_file(file, file_length, file.tell())
        elif file_name == "offset":
            # skip over this LEL
            file.seek(file_length, 1)
        elif file_name == "xrefs":
            read_xrefs(file)
        else:
            # assume geometry
            read_geometry_file(file, file_name)
    # END READ PKG FILE DATA

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
