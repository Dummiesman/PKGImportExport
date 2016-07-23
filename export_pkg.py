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
from io_scene_pkg.fvf import FVF

global pkg_path
pkg_path = None

global apply_modifiers_G
apply_modifiers_G = True

######################################################
# GLOBAL LISTS
######################################################

# AI/Player Vehicle
vehicle_list = ["BODY_H", "BODY_M", "BODY_L", "BODY_VL",
                "SHADOW_H", "SHADOW_M", "SHADOW_L", "SHADOW_VL",
                "HLIGHT_H", "HLIGHT_M", "HLIGHT_L", "HLIGHT_VL",
                "TLIGHT_H", "TLIGHT_M", "TLIGHT_L", "TLIGHT_VL",
                "SLIGHT0_H", "SLIGHT0_M", "SLIGHT0_L", "SLIGHT0_VL",
                "SLIGHT1_H", "SLIGHT1_M", "SLIGHT1_L", "SLIGHT1_VL",
                "RLIGHT_H", "RLIGHT_M", "RLIGHT_L", "RLIGHT_VL",
                "BLIGHT_H", "BLIGHT_M", "BLIGHT_L", "BLIGHT_VL",
                "SIREN0_H", "SIREN0_M", "SIREN0_L", "SIREN0_VL",
                "SIREN1_H", "SIREN1_M", "SIREN1_L", "SIREN1_VL",
                "WHL0_H", "WHL0_M", "WHL0_L", "WHL0_VL",
                "WHL1_H", "WHL1_M", "WHL1_L", "WHL1_VL",
                "WHL2_H", "WHL2_M", "WHL2_L", "WHL2_VL",
                "WHL3_H", "WHL3_M", "WHL3_L", "WHL3_VL",
                "WHL4_H", "WHL4_M", "WHL4_L", "WHL4_VL",
                "WHL5_H", "WHL5_M", "WHL5_L", "WHL5_VL",
                "BREAK0_H", "BREAK0_M", "BREAK0_L", "BREAK0_VL",
                "BREAK1_H", "BREAK1_M", "BREAK1_L", "BREAK1_VL",
                "BREAK2_H", "BREAK2_M", "BREAK2_L", "BREAK2_VL",
                "BREAK3_H", "BREAK3_M", "BREAK3_L", "BREAK3_VL",
                "BREAK01_H", "BREAK01_M", "BREAK01_L", "BREAK01_VL",
                "BREAK12_H", "BREAK12_M", "BREAK12_L", "BREAK12_VL",
                "BREAK23_H", "BREAK23_M", "BREAK23_L", "BREAK23_VL",
                "BREAK03_H", "BREAK03_M", "BREAK03_L", "BREAK03_VL",
                "TRAILER_HITCH_H", "TRAILER_HITCH_M", "TRAILER_HITCH_L", "TRAILER_HITCH_VL",
                "SRN0_H", "SRN0_M", "SRN0_L", "SRN0_VL",
                "SRN1_H", "SRN1_M", "SRN1_L", "SRN1_VL",
                "SRN2_H", "SRN2_M", "SRN2_L", "SRN2_VL",
                "SRN3_H", "SRN3_M", "SRN3_L", "SRN3_VL",
                "HEADLIGHT0_H", "HEADLIGHT0_M", "HEADLIGHT0_L", "HEADLIGHT0_VL",
                "HEADLIGHT1_H", "HEADLIGHT1_M", "HEADLIGHT1_L", "HEADLIGHT1_VL"
                "FNDR0_H", "FNDR0_M", "FNDR0_L", "FNDR0_VL",
                "FNDR1_H", "FNDR1_M", "FNDR1_L", "FNDR1_VL"]

# Vehicle Dashboards
dash_list = ["DAMAGE_NEEDLE_H", "DAMAGE_NEEDLE_M", "DAMAGE_NEEDLE_L", "DAMAGE_NEEDLE_VL",
             "DASH_H", "DASH_M", "DASH_L", "DASH_VL",
             "GEAR_INDICATOR_H", "GEAR_INDICATOR_M", "GEAR_INDICATOR_L", "GEAR_INDICATOR_VL",
             "ROOF_H", "ROOF_M", "ROOF_L", "ROOF_VL",
             "SPEED_NEEDLE_H", "SPEED_NEEDLE_M", "SPEED_NEEDLE_L", "SPEED_NEEDLE_VL",
             "TACH_NEEDLE_H", "TACH_NEEDLE_M", "TACH_NEEDLE_L", "TACH_NEEDLE_VL",
             "WHEEL_H", "WHEEL_M", "WHEEL_L", "WHEEL_VL"]

# Vehicle trailers
trailer_list = ["TRAILER_H", "TRAILER_M", "TRAILER_L", "TRAILER_VL",
                "SHADOW_H", "SHADOW_M", "SHADOW_L", "SHADOW_VL",
                "TLIGHT_H", "TLIGHT_M", "TLIGHT_L", "TLIGHT_VL",
                "TWHL0_H", "TWHL0_M", "TWHL0_L", "TWHL0_VL",
                "TWHL1_H", "TWHL1_M", "TWHL1_L", "TWHL1_VL",
                "TWHL2_H", "TWHL2_M", "TWHL2_L", "TWHL2_VL",
                "TWHL3_H", "TWHL3_M", "TWHL3_L", "TWHL3_VL",
                "TRAILER_HITCH_H", "TRAILER_HITCH_M", "TRAILER_HITCH_L", "TRAILER_HITCH_VL"]

# Props, buildings, etc
generic_list = ["H", "M", "L", "VL",
                "BREAK01_H", "BREAK01_M", "BREAK01_L", "BREAK01_VL",
                "BREAK02_H", "BREAK02_M", "BREAK02_L", "BREAK02_VL",
                "BREAK03_H", "BREAK03_M", "BREAK03_L", "BREAK03_VL",
                "BREAK04_H", "BREAK04_M", "BREAK04_L", "BREAK04_VL",
                "BREAK05_H", "BREAK05_M", "BREAK05_L", "BREAK05_VL",
                "BREAK06_H", "BREAK06_M", "BREAK06_L", "BREAK06_VL",
                "BREAK07_H", "BREAK07_M", "BREAK07_L", "BREAK07_VL",
                "BREAK08_H", "BREAK08_M", "BREAK08_L", "BREAK08_VL",
                "BREAK09_H", "BREAK09_M", "BREAK09_L", "BREAK09_VL",
                "REDGLOWDAY_H", "REDGLOWDAY_M", "REDGLOWDAY_L", "REDGLOWDAY_VL",
                "YELLOWGLOWDAY_H", "YELLOWGLOWDAY_M", "YELLOWGLOWDAY_L", "YELLOWGLOWDAY_VL",
                "GREENGLOWDAY_H", "GREENGLOWDAY_M", "GREENGLOWDAY_L", "GREENGLOWDAY_VL",
                "WALK_DAY_H", "WALK_DAY_M", "WALK_DAY_L", "WALK_DAY_VL",
                "NOWALK_DAY_H", "NOWALK_DAY_M", "NOWALK_DAY_L", "NOWALK_DAY_VL",
                "REDGLOWNIGHT_H", "REDGLOWNIGHT_M", "REDGLOWNIGHT_L", "REDGLOWNIGHT_VL",
                "YELLOWGLOWNIGHT_H", "YELLOWGLOWNIGHT_M", "YELLOWGLOWNIGHT_L", "YELLOWGLOWNIGHT_VL",
                "GREENGLOWNIGHT_H", "GREENGLOWNIGHT_M", "GREENGLOWNIGHT_L", "GREENGLOWNIGHT_VL",
                "WALK_NIGHT_H", "WALK_NIGHT_M", "WALK_NIGHT_L", "WALK_NIGHT_VL",
                "NOWALK_NIGHT_H", "NOWALK_NIGHT_M", "NOWALK_NIGHT_L", "NOWALK_NIGHT_VL"]

# do not export' list
dne_list = ["BOUND", "BINARY_BOUND",
            "EXHAUST0_H", "EXHAUST0_M", "EXHAUST0_L", "EXHAUST0_VL",
            "EXHAUST1_H", "EXHAUST1_M", "EXHAUST1_L", "EXHAUST1_VL"]

######################################################
# EXPORT HELPERS
######################################################
def reorder_objects(lst, pred):
    return_list = [None] * len(pred)
    for v in lst:
        try:
            return_list[pred.index(v.name)] = v
        except:
            # not found in predicate list
            return_list.append(v)
    return [x for x in return_list if x is not None]


def write_angel_string(file, strng):
    str_len = len(strng)
    if str_len > 0:
        file.write(struct.pack('B', str_len+1))
        file.write(bytes(strng, 'UTF-8'))
        file.write(bytes('\x00', 'UTF-8'))
    else:
        file.write(struct.pack('B', 0))


def write_color(file, color):
    file.write(struct.pack('BBBB', int(color[0] * 255), int(color[1] * 255), int(color[2] * 255), 255))


def write_file_header(file, name, length=0):
    file.write(bytes('FILE', 'utf-8'))
    write_angel_string(file, name)
    file.write(struct.pack('L', length))


def get_undupe_name(name):
    nidx = name.find('.')
    return name[:nidx] if nidx != -1 else name


def get_material_offset(mtl):
    # :( hack
    coffset = 0
    for mat in bpy.data.materials:
        if mtl.name == mat.name:
            return coffset
        coffset += 1
    return -1


def get_raw_object_name(meshname):
    # strip out _H _M _L _VL text
    return meshname.replace("_VL", "").replace("_L", "").replace("_M", "").replace("_H", "")


def get_replace_words(rpl_str):
    if len(rpl_str) == 0:
        return []
    base_list = rpl_str.split('|')
    ret_list = [None] * len(base_list)
    for num in range(len(base_list)):
        v = base_list[num].split(',')
        if(len(v) < 2):
            v.append(v[0])
        ret_list[num] = v
    return ret_list


def bounds(obj):

    local_coords = obj.bound_box[:]
    om = obj.matrix_world
    coords = [p[:] for p in local_coords]

    rotated = zip(*coords[::-1])

    push_axis = []
    for (axis, _list) in zip('xyz', rotated):
        info = lambda: None
        info.max = max(_list)
        info.min = min(_list)
        info.distance = info.max - info.min
        push_axis.append(info)

    import collections

    originals = dict(zip(['x', 'y', 'z'], push_axis))

    o_details = collections.namedtuple('object_details', 'x y z')
    return o_details(**originals)


def write_matrix(meshname, object):
    mesh_name_parsed = get_raw_object_name(meshname)
    find_path = pkg_path[:-4] + '_' + mesh_name_parsed + ".mtx"
    # get bounds
    bnds = bounds(object)
    mtxfile = open(find_path, 'wb')
    mtxfile.write(struct.pack('ffffffffffff', bnds.x.min,
                                              bnds.z.min,
                                              bnds.y.min * -1,
                                              bnds.x.max,
                                              bnds.z.max,
                                              bnds.y.max * -1,
                                              # export location twice :/
                                              # since Blender seems to use that for Location and origin
                                              object.location.x,
                                              object.location.z,
                                              object.location.y * -1,
                                              object.location.x,
                                              object.location.z,
                                              object.location.y * -1))
    mtxfile.close()
    return


def clean_object_materials():
    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    for ob in bpy.data.objects:
        if ob.type != 'MESH':
            continue
        mat_slots = {}
        for p in ob.data.polygons:
            mat_slots[p.material_index] = 1
        mat_slots = mat_slots.keys()
        for i in reversed(range(len(ob.material_slots))):
            if i not in mat_slots:
                bpy.context.scene.objects.active = ob
                ob.data.materials.pop(i)


def find_object_ci(name):
    for obj in bpy.data.objects:
        if obj.name.lower() == name.lower():
            return obj
    return None

######################################################
# EXPORT MAIN FILES
######################################################
def autobound():
    # check if our directory exists
    bounddir = path.abspath(path.join(os.path.dirname(pkg_path), "../bound"))
    if not os.path.exists(bounddir):
        os.makedirs(bounddir)
    boundpath = bounddir + '\\' + (os.path.basename(pkg_path)[:-4]) + '_BOUND.bnd'
    # vehicles only
    bodyobj = find_object_ci('BODY_H')
    if bodyobj is not None:
        bnds = bounds(bodyobj)
        veh_rear_max = round(bnds.y.min, 6)
        veh_front_max = round(bnds.y.max, 6)
        # offset the bottom a bit since the front+rear tends to be higher
        veh_bottom = round(bnds.z.min + 0.03, 6)
        veh_center = round((bnds.y.min + bnds.y.max) / 2, 6)
        tpf_height = 0.0
        tpr_height = 0.0
        tpm_height = 0.0
        left_coord = round(bnds.x.min, 6)
        right_coord = round(bnds.x.max, 6)
        # find 3 height values
        for v in bodyobj.data.vertices:
            co = v.co
            if co[1] > (veh_front_max - 0.2) and co[2] > tpf_height:
                tpf_height = round(co[2], 6)
            if co[1] < veh_front_max and co[1] > veh_rear_max and co[2] > tpm_height:
                tpm_height = round(co[2], 6)
            if co[1] < (veh_rear_max + 0.2) and co[2] > tpr_height:
                tpr_height = round(co[2], 6)
        # write bound file
        bound_file = ("version: 1.01\n"
                      "verts: 10\n"
                      "materials: 1\n"
                      "edges: 0\n"
                      "polys: 16\n")
        # write vertices
        bound_file += "v " + str(left_coord) + ' ' + str(veh_bottom) + ' ' + str(veh_front_max * -1)
        bound_file += "\nv " + str(right_coord) + ' ' + str(veh_bottom) + ' ' + str(veh_front_max * -1)
        bound_file += "\nv " + str(left_coord) + ' ' + str(veh_bottom) + ' ' + str(veh_rear_max * -1)
        bound_file += "\nv " + str(right_coord) + ' ' + str(veh_bottom) + ' ' + str(veh_rear_max * -1)
        bound_file += "\nv " + str(left_coord) + ' ' + str(tpf_height) + ' ' + str(veh_front_max * -1)
        bound_file += "\nv " + str(left_coord) + ' ' + str(tpr_height) + ' ' + str(veh_rear_max * -1)
        bound_file += "\nv " + str(left_coord) + ' ' + str(tpm_height) + ' ' + str(veh_center * -1)
        bound_file += "\nv " + str(right_coord) + ' ' + str(tpf_height) + ' ' + str(veh_front_max * -1)
        bound_file += "\nv " + str(right_coord) + ' ' + str(tpr_height) + ' ' + str(veh_rear_max * -1)
        bound_file += "\nv " + str(right_coord) + ' ' + str(tpm_height) + ' ' + str(veh_center * -1)
        # write material
        bound_file += ("\n\nmtl default {\n"
                       "\telasticity: 0.1\n"
                       "\tfriction: 0.5\n"
                       "\teffect: none\n"
                       "\tsound: 0\n"
                       "}\n\n"
                       "tri\t1   2   0   0\n"
                       "tri\t3   2   1   0\n"
                       "tri\t0   2   5   0\n"
                       "tri\t0   5   4   0\n"
                       "tri\t4   5   6   0\n"
                       "tri\t1   0   4   0\n"
                       "tri\t7   1   4   0\n"
                       "tri\t7   4   6   0\n"
                       "tri\t6   9   7   0\n"
                       "tri\t5   8   6   0\n"
                       "tri\t8   9   6   0\n"
                       "tri\t5   2   3   0\n"
                       "tri\t3   8   5   0\n"
                       "tri\t1   8   3   0\n"
                       "tri\t1   7   8   0\n"
                       "tri\t8   7   9   0")

        with open(boundpath, "w") as text_file:
            text_file.write(bound_file)

    else:
        print('Error : Cannot create auto bound because no BODY_H in scene!')


def export_xrefs(file):
    has_xrefs = False
    for obj in bpy.data.objects:
        if obj.name.startswith("xref:"):
            has_xrefs = True
            break
    if has_xrefs:
        write_file_header(file, "xrefs")
        num_xrefs = 0
        xref_num_offset = file.tell()
        file.write(struct.pack('L', 0))
        for obj in bpy.data.objects:
            if obj.name.startswith("xref:"):
                num_xrefs += 1
                # write null matrices
                file.write(struct.pack('fffffffff', 0, 0, 0, 0, 0, 0, 0, 0, 0))
                # convert location and write it
                file.write(struct.pack('fff', obj.location[0], obj.location[2], obj.location[1] * -1))
               
                # write xref name
                xref_name = get_undupe_name(obj.name[5:]) + ".max"
                null_length = 32 - len(xref_name)
                
                file.write(bytes(xref_name, 'utf-8'))
                file.write(bytes('\x00' * null_length, 'utf-8'))
        file_length = file.tell() - xref_num_offset
        file.seek(xref_num_offset - 4, 0)
        file.write(struct.pack('LL', file_length, num_xrefs))
        file.seek(0, 2)
    else:
        return


def export_offset(file):
    write_file_header(file, "offset", 12)
    file.write(struct.pack('fff', 0, 0, 0))


def export_shaders(file, replace_words, type="byte"):
    # First paintjob replace word. If this isn't added we get paintjobs-1 paintjobs :(
    replace_words.insert(0, ['$!*%&INVALIDMATERIAL&%*!$', '$!*%&INVALIDMATERIAL&%*!$'])
    # write file header and record offset
    write_file_header(file, "shaders")
    shaders_data_offset = file.tell()
    # prepare shaders header
    shadertype_raw = len(replace_words)
    if type == "byte":
        shadertype_raw += 128
    shaders_per_paintjob = len(bpy.data.materials)
    # write header
    file.write(struct.pack('LL', shadertype_raw, shaders_per_paintjob))
    # write material sets
    for rwa in replace_words:
        # export a material set
        for mtl in bpy.data.materials:
            bname = mtl.name
            if mtl.active_texture is not None:
                bname = mtl.active_texture.name  # use texture name instead
            mtl_name = get_undupe_name(mtl.name.replace(rwa[0], rwa[1]))
            if mtl_name.startswith('mm2:notexture') or mtl_name.startswith('age:notexture'):
                # matte material
                write_angel_string(file, '')
            else:
                # has texture
                write_angel_string(file, mtl_name)

            # calculate alpha for writing
            mtl_alpha = 1
            if mtl.use_transparency:
                mtl_alpha -= mtl.alpha

            if type == "byte":
                file.write(struct.pack('BBBB', int(mtl.diffuse_color[0] * 255), int(mtl.diffuse_color[1] * 255), int(mtl.diffuse_color[2] * 255), int(mtl_alpha * 255)))
                file.write(struct.pack('BBBB', int(mtl.diffuse_color[0] * 255), int(mtl.diffuse_color[1] * 255), int(mtl.diffuse_color[2] * 255), int(mtl_alpha * 255)))
                file.write(struct.pack('BBBB', int(mtl.specular_color[0] * 255), int(mtl.specular_color[1] * 255), int(mtl.specular_color[2] * 255), 255))
            elif type == "float":
                file.write(struct.pack('ffff', mtl.diffuse_color[0], mtl.diffuse_color[1], mtl.diffuse_color[2], mtl_alpha))
                file.write(struct.pack('ffff', mtl.diffuse_color[0], mtl.diffuse_color[1], mtl.diffuse_color[2], mtl_alpha))
                file.write(struct.pack('ffff', mtl.specular_color[0], mtl.specular_color[1], mtl.specular_color[2], 1))
                # ????
                file.write(struct.pack('ffff', 0, 0, 0, 1))

            # shininess
            file.write(struct.pack('f', mtl.raytrace_mirror.reflect_factor))

    # write file length
    shaders_file_length = file.tell() - shaders_data_offset
    file.seek(shaders_data_offset - 4)
    file.write(struct.pack('L', shaders_file_length))
    file.seek(0, 2)


def export_meshes(file, meshlist, options):
    for obj in meshlist:
        # write FILE header for mesh name
        write_file_header(file, obj.name)
        file_data_start_offset = file.tell()
        
        # create temp mesh
        temp_mesh = obj.to_mesh(bpy.context.scene, apply_modifiers_G, 'PREVIEW')
        
        # get bmesh
        bm = bmesh.new()
        bm.from_mesh(temp_mesh)
        bm_tris = bm.calc_tessface()
        # get mesh infos
        total_verts = len(bm.verts)
        total_faces = int(len(bm_tris) * 3)
        num_sections = len(obj.data.materials)
        
        #build FVF
        FVF_FLAGS = FVF(("D3DFVF_XYZ", "D3DFVF_NORMAL", "D3DFVF_TEX1"))
        for mat in obj.data.materials:
            if mat.use_shadeless:
                # undo the previous flag since we arent
                # going to write normals
                FVF_FLAGS.clear_flag("D3DFVF_NORMAL")
                break
        if "VC_DIFFUSE" in options:
            FVF_FLAGS.set_flag("D3DFVF_DIFFUSE")
        if "VC_SPECULAR" in options:
            FVF_FLAGS.set_flag("D3DFVF_SPECULAR")

        # do we need a matrix file. Only for H object
        if ((obj.location[0] != 0 or obj.location[1] != 0 or obj.location[2] != 0) and obj.name.upper().endswith("_H")):
            write_matrix(obj.name, obj)

        # write mesh data header
        file.write(struct.pack('LLLLL', num_sections, total_verts, total_faces, num_sections, FVF_FLAGS.value))

        # write sections
        cmtl_index = 0
        for mat in obj.data.materials:
            # build the mesh data we need
            uv_layer = bm.loops.layers.uv.active
            vc_layer = bm.loops.layers.color.active

            # initialize lists for conversion
            cmtl_indices = []
            cmtl_tris = []
            cmtl_verts = []
            cmtl_uvs = []
            cmtl_cols = []
            
            # build tris that are in this material pass
            for lt in bm_tris:
                if lt[0].face.material_index == cmtl_index:
                  cmtl_tris.append(lt)
            
            # BECAUSE THIS GAME WANTS VERT INDEXES AND NOT FACE INDEXES D:
            index_remap_table = {}
            for lt in cmtl_tris:
                #funstuff :|
                indices = [-1, -1, -1]
                for x in range(3):
                    l = lt[x]
                    # prepare our hash entry
                    uv_hash = "NOUV"
                    col_hash = "NOCOL"
                    pos_hash = str(l.vert.co)
                    nrm_hash = str(l.vert.normal)
                    if uv_layer is not None:
                        uv_hash = str(l[uv_layer].uv)
                    if vc_layer is not None:
                        col_hash = str(l[vc_layer])
                    index_hash = uv_hash + "|" + col_hash + "|" + pos_hash + "|" + nrm_hash

                    # do we already have a vertex for this?
                    if index_hash in index_remap_table:
                        indices[x] = index_remap_table[index_hash]
                    else:
                        # get what our next index will be and append to remap table
                        next_index = len(cmtl_verts)
                        index_remap_table[index_hash] = next_index
                        indices[x] = next_index

                        # add neccessary data to remapping tables
                        cmtl_verts.append(l.vert)

                        if uv_layer is not None:
                            cmtl_uvs.append(l[uv_layer].uv)
                        else:
                            cmtl_uvs.append((0,0))

                        if vc_layer is not None:
                            cmtl_cols.append(l[vc_layer])
                        else:
                            cmtl_cols.append((0,0,0,0))

                # finally append this triangle                
                cmtl_indices.append(indices)        

            # mesh remap done. we will now write our strip
            num_strips = 1
            section_flags = 0
            shader_offset = get_material_offset(mat)
            # write strip to file
            file.write(struct.pack('HHL', num_strips, section_flags, shader_offset))
            strip_primType = 3
            strip_vertices = len(cmtl_verts)
            file.write(struct.pack('LL', strip_primType, strip_vertices))
            for cv in range(len(cmtl_verts)):
                export_vert = cmtl_verts[cv]
                file.write(struct.pack('fff', export_vert.co[0], export_vert.co[2], export_vert.co[1] * -1))
                if FVF_FLAGS.has_flag("D3DFVF_NORMAL"):
                    file.write(struct.pack('fff', export_vert.normal[0], export_vert.normal[2], export_vert.normal[1] * -1))
                if FVF_FLAGS.has_flag("D3DFVF_DIFFUSE"):
                    write_color(file, cmtl_cols[cv])
                if FVF_FLAGS.has_flag("D3DFVF_SPECULAR"):
                    write_color(file, cmtl_cols[cv])
                uv_data = cmtl_uvs[cv]
                file.write(struct.pack('ff', uv_data[0], (uv_data[1] - 1) * -1))
                
            strip_indices_len = int(len(cmtl_indices) * 3)
            file.write(struct.pack('L', strip_indices_len))
            for ply in cmtl_indices:
                file.write(struct.pack('HHH', ply[0], ply[1], ply[2]))
            cmtl_index += 1
        
        # clean up temp_mesh
        bpy.data.meshes.remove(temp_mesh)
            
        # write FILE length
        file_data_length = file.tell() - file_data_start_offset
        file.seek(file_data_start_offset - 4)
        file.write(struct.pack('L', file_data_length))
        file.seek(0, 2)

######################################################
# EXPORT
######################################################
def save_pkg(filepath,
             paintjobs,
             g_autobound,
             e_vertexcolors,
             e_vertexcolors_s,
             context):
    global pkg_path
    pkg_path = filepath

    print("exporting PKG: %r..." % (filepath))

    if bpy.ops.object.select_all.poll():
        bpy.ops.object.select_all(action='DESELECT')

    time1 = time.clock()
    file = open(filepath, 'wb')
    
    # create our options list
    export_options = []
    if e_vertexcolors:
        export_options.append("VC_DIFFUSE")
    if e_vertexcolors_s:
        export_options.append("VC_SPECULAR")
    
    # first we need to figure out the export type before anything
    export_pred = generic_list
    export_typestr = 'generic'
    export_shadertype = 'byte'
    for obj in bpy.data.objects:
        if (obj.type == 'MESH'):
            # we can check this object :)
            if obj.name.upper().startswith("DASH_"):
                export_shadertype = 'float'
                export_typestr = 'dash'
                export_pred = dash_list
                break
            if obj.name.upper().startswith("BODY_"):
                export_typestr = 'vehicle'
                export_pred = vehicle_list
                break
            if obj.name.upper().startswith("TRAILER_"):
                export_typestr = 'trailer'
                export_pred = trailer_list
                break
    print('\tPKG autodetected export type: ' + export_typestr)
    
    # unlink any unused materials at object level
    clean_object_materials()
    # remove any unused materials at scene level
    # this deletes unlinked materials from the
    # previous step
    for material in bpy.data.materials:
        if not material.users:
            bpy.data.materials.remove(material)

    # next we need to prepare our mesh list
    export_meshlist = []
    for obj in bpy.data.objects:
        if (obj.type == 'MESH' and not obj.name.upper() in dne_list):
            export_meshlist.append(obj)

    # WRITE PKG FILE
    file.write(bytes('PKG3', 'utf-8'))
    print('\t[%.4f] exporting mesh data' % (time.clock() - time1))
    export_meshes(file, reorder_objects(export_meshlist, export_pred), export_options)
    print('\t[%.4f] exporting shaders' % (time.clock() - time1))
    export_shaders(file, get_replace_words(paintjobs), export_shadertype)
    print('\t[%.4f] exporting xrefs' % (time.clock() - time1))
    export_xrefs(file)
    print('\t[%.4f] exporting offset' % (time.clock() - time1))
    export_offset(file)
    if g_autobound:
        print('\t[%.4f] creating bound' % (time.clock() - time1))
        autobound()
    # PKG WRITE DONE
    print(" done in %.4f sec." % (time.clock() - time1))
    file.close()


def save(operator,
         context,
         filepath="",
         additional_paintjobs="",
         g_autobound=False,
         e_vertexcolors=False,
         e_vertexcolors_s=False,
         apply_modifiers=False
         ):
    
    
    # set globals
    global apply_modifiers_G
    apply_modifiers_G = apply_modifiers
    
    # save PKG
    save_pkg(filepath,
             additional_paintjobs,
             g_autobound,
             e_vertexcolors,
             e_vertexcolors_s,
             context,
             )

    return {'FINISHED'}
