# ##### BEGIN LICENSE BLOCK #####
#
# This program is licensed under Creative Commons BY-NC-SA:
# https://creativecommons.org/licenses/by-nc-sa/3.0/
#
# Copyright (C) Dummiesman, 2016
#
# ##### END LICENSE BLOCK #####

import bpy, bmesh, mathutils
import os, time, struct

import os.path as path
from mathutils import*
from io_scene_pkg.fvf import FVF

import io_scene_pkg.binary_helper as bin
import io_scene_pkg.import_helper as helper

global pkg_path
pkg_path = None

######################################################
# IMPORT MAIN FILES
######################################################
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
        texture_name = bin.read_angel_string(file)
        if texture_name == '':
            # matte material
            texture_name = "age:notexture"
        
        # initialize these
        diffuse_color = None
        specular_color = None
        if shader_type == "float":
            diffuse_color = bin.read_color4f(file)
            file.seek(16,1) # seek past"" diffuse""
            specular_color = bin.read_color4f(file)
            file.seek(16,1) # seek past unused reflective color
        elif shader_type == "byte":
            diffuse_color = bin.read_color4d(file)
            file.seek(4,1) # seek past ""diffuse""            
            specular_color = bin.read_color4d(file)
        shininess = bin.read_float(file)

        # insert this data
        mtl = bpy.data.materials.get(str(num))
        if mtl is not None:
            # setup colors
            mtl.diffuse_color = (diffuse_color[0], diffuse_color[1], diffuse_color[2])
            mtl.specular_color = (specular_color[0], specular_color[1], specular_color[2])
            mtl.specular_intensity = 0.1
            mtl.raytrace_mirror.reflect_factor = shininess
            
            # have alpha?
            mtl_alpha_test = diffuse_color[3]
            if mtl_alpha_test < 1:
                mtl.use_transparency = True
                mtl.alpha = mtl_alpha_test
                
            # look for a texture
            tex_result = helper.try_load_texture(texture_name, pkg_path)
            if tex_result is not False:
                cTex = bpy.data.textures.new(texture_name, type='IMAGE')
                cTex.image = tex_result
                
                mtex = mtl.texture_slots.add()
                mtex.texture = cTex
                mtex.blend_type = 'MULTIPLY'
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
        xref_position = bin.read_float3(file)
        xref_name = file.read(32).decode("utf-8")
        ob = bpy.data.objects.new("xref:" + xref_name, None)
        ob.location = (xref_position[0], xref_position[2] * -1, xref_position[1])
        ob.show_name = True
        ob.show_axis = True
        scn.objects.link(ob)


def read_geometry_file(file, meshname):
    scn = bpy.context.scene
    # add a mesh and link it to the scene
    me = bpy.data.meshes.new(meshname+'Mesh')
    ob = bpy.data.objects.new(meshname, me)

    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    
    # create layers for this object
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
        num_strips, strip_flags = struct.unpack('HH', file.read(4))
        
        # strip flags
        FLAG_compact_strips = ((strip_flags & (1 << 8)) != 0)
        
        # fvf flags
        FVF_FLAGS = FVF(fvf)

        shader_offset = 0
        if FLAG_compact_strips:
            shader_offset = struct.unpack('H', file.read(2))[0]
        else:
            shader_offset = struct.unpack('L', file.read(4))[0]
        
        # do we have this material?
        if bpy.data.materials.get(str(shader_offset)) is None:
            # we must make it!
            bpy.data.materials.new(name=str(shader_offset))
        
        ob.data.materials.append(bpy.data.materials.get(str(shader_offset)))
        ob_current_material += 1
        
        # read strip data
        if FLAG_compact_strips:
            ############################
            # READ MIDNIGHT CLUB STRIP #
            ############################
            for num2 in range(num_strips):
                # primtype
                file.seek(2, 1)
                num_vertices = struct.unpack('H', file.read(2))[0]
                for i in range(num_vertices):
                    vpos = bin.read_float3(file)
                    vnorm, vuv, vcolor = helper.read_vertex_data(file, FVF_FLAGS, True)

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
                
                # convert all our strips
                trilist_data = helper.convert_triangle_strips(tristrip_data)
                
                #build mesh polygons
                for i in range(0, len(trilist_data), 3):
                    read_indices = (trilist_data[i] + current_vert_offset, trilist_data[i+1] + current_vert_offset, trilist_data[i+2] + current_vert_offset)
                    try:
                        face = bm.faces.new((bm.verts[read_indices[0]], bm.verts[read_indices[1]], bm.verts[read_indices[2]]))
                        face.smooth = True
                        face.material_index = ob_current_material
                        
                        # set uvs
                        for uv_set_loop in range(3):
                          face.loops[uv_set_loop][uv_layer].uv = uvs[read_indices[uv_set_loop]]
                          
                        # set colors
                        for color_set_loop in range(3):
                          face.loops[color_set_loop][vc_layer] = colors[read_indices[color_set_loop]]
                    except Exception as e:
                        print(str(e))

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
                    vpos = bin.read_float3(file)
                    vnorm, vuv, vcolor = helper.read_vertex_data(file, FVF_FLAGS, False)
                    
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
                    read_indices = (face_data[0] + current_vert_offset, face_data[1] + current_vert_offset, face_data[2] + current_vert_offset)
                    try:
                        face = bm.faces.new((bm.verts[read_indices[0]], bm.verts[read_indices[1]], bm.verts[read_indices[2]]))
                        face.smooth = True
                        face.material_index = ob_current_material
                        # set uvs
                        for uv_set_loop in range(3):
                          face.loops[uv_set_loop][uv_layer].uv = uvs[read_indices[uv_set_loop]]
                          
                        # set colors
                        for color_set_loop in range(3):
                          face.loops[color_set_loop][vc_layer] = colors[read_indices[color_set_loop]]
                    except Exception as e:
                        print(str(e))

                current_vert_offset += num_vertices

    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    bm.to_mesh(me)
    bm.free()
    # lastly, look for a MTX file
    helper.find_matrix(meshname, ob, pkg_path)
    return

######################################################
# IMPORT
######################################################
def load_pkg(filepath,
             context):
    # set the PKG path, used for finding textures
    global pkg_path
    pkg_path = filepath

    print("importing PKG: %r..." % (filepath))

    if bpy.ops.object.select_all.poll():
        bpy.ops.object.select_all(action='DESELECT')

    time1 = time.clock()
    file = open(filepath, 'rb')

    # start reading our pkg file
    PKGTYPE = file.read(4).decode("utf-8")
    if PKGTYPE != "PKG3":
        print('\tFatal Error:  PKG file is wrong format : ' + PKGTYPE)
        file.close()
        return

    # read pkg FILE's
    pkg_size = path.getsize(filepath)
    while file.tell() != pkg_size:
        file_header = file.read(4).decode("utf-8")

        # check for an invalid header
        if file_header != "FILE":
            print('\tFatal Error: PKG file is corrupt, missing FILE header at ' + str(file.tell()))
            file.close()
            return

        # found a proper FILE header
        file_name = bin.read_angel_string(file)
        file_length = struct.unpack('L', file.read(4))[0]
        
        # Angel released a very small batch of corrupt PKG files
        # this is here just in case someone tries to import one
        if file_length == 0:
            raise Exception("Invalid PKG3 file : cannot have file length of 0")
            
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
