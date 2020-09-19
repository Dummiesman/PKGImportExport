# ##### BEGIN LICENSE BLOCK #####
#
# This program is licensed under Creative Commons BY-NC-SA:
# https://creativecommons.org/licenses/by-nc-sa/3.0/
#
# Created by Dummiesman, 2016-2020
#
# ##### END LICENSE BLOCK #####

import bpy, bmesh
import os, time, struct

import os.path as path

from io_scene_pkg.fvf import FVF

import io_scene_pkg.binary_helper as bin
import io_scene_pkg.export_helper as export_helper
import io_scene_pkg.common_helpers as helper

from io_scene_pkg.shader_set import (ShaderSet, Shader)

# globals
global pkg_path
pkg_path = None

global material_remap_table
material_remap_table = {}


######################################################
# GLOBAL LISTS
######################################################

# AI/Player Vehicle
vehicle_list = ["BODY_H", "BODY_M", "BODY_L", "BODY_VL",
                "SHADOW_H", "SHADOW_M", "SHADOW_L", "SHADOW_VL",
                "HLIGHT_H", "HLIGHT_M", "HLIGHT_L", "HLIGHT_VL",
                "TLIGHT_H", "TLIGHT_M", "TLIGHT_L", "TLIGHT_VL",
                "RLIGHT_H", "RLIGHT_M", "RLIGHT_L", "RLIGHT_VL",
                "SLIGHT0_H", "SLIGHT0_M", "SLIGHT0_L", "SLIGHT0_VL",
                "SLIGHT1_H", "SLIGHT1_M", "SLIGHT1_L", "SLIGHT1_VL",
                "BLIGHT_H", "BLIGHT_M", "BLIGHT_L", "BLIGHT_VL",
                "BODYDAMAGE_H", "BODYDAMAGE_M", "BODYDAMAGE_L", "BODYDAMAGE_VL",
                "SIREN0_H", "SIREN0_M", "SIREN0_L", "SIREN0_VL",
                "SIREN1_H", "SIREN1_M", "SIREN1_L", "SIREN1_VL",
                "DECAL_H", "DECAL_M", "DECAL_L", "DECAL_VL",
                "DRIVER_H", "DRIVER_M", "DRIVER_L", "DRIVER_VL",
                "SHOCK0_H", "SHOCK0_M", "SHOCK0_L", "SHOCK0_VL",
                "SHOCK1_H", "SHOCK1_M", "SHOCK1_L", "SHOCK1_VL",
                "SHOCK2_H", "SHOCK2_M", "SHOCK2_L", "SHOCK2_VL",
                "SHOCK3_H", "SHOCK3_M", "SHOCK3_L", "SHOCK3_VL",
                "ARM0_H", "ARM0_M", "ARM0_L", "ARM0_VL",
                "ARM1_H", "ARM1_M", "ARM1_L", "ARM1_VL",
                "ARM2_H", "ARM2_M", "ARM2_L", "ARM2_VL",
                "ARM3_H", "ARM3_M", "ARM3_L", "ARM3_VL",
                "SHAFT2_H", "SHAFT2_M", "SHAFT2_L", "SHAFT2_VL",
                "SHAFT3_H", "SHAFT3_M", "SHAFT3_L", "SHAFT3_VL",
                "AXLE0_H", "AXLE0_M", "AXLE0_L", "AXLE0_VL",
                "AXLE1_H", "AXLE1_M", "AXLE1_L", "AXLE1_VL",
                "ENGINE_H", "ENGINE_M", "ENGINE_L", "ENGINE_VL",
                "WHL0_H", "WHL0_M", "WHL0_L", "WHL0_VL",
                "WHL1_H", "WHL1_M", "WHL1_L", "WHL1_VL",
                "WHL2_H", "WHL2_M", "WHL2_L", "WHL2_VL",
                "WHL3_H", "WHL3_M", "WHL3_L", "WHL3_VL",
                "BREAK0_H", "BREAK0_M", "BREAK0_L", "BREAK0_VL",
                "BREAK1_H", "BREAK1_M", "BREAK1_L", "BREAK1_VL",
                "BREAK2_H", "BREAK2_M", "BREAK2_L", "BREAK2_VL",
                "BREAK3_H", "BREAK3_M", "BREAK3_L", "BREAK3_VL",
                "BREAK01_H", "BREAK01_M", "BREAK01_L", "BREAK01_VL",
                "BREAK12_H", "BREAK12_M", "BREAK12_L", "BREAK12_VL",
                "BREAK23_H", "BREAK23_M", "BREAK23_L", "BREAK23_VL",
                "BREAK03_H", "BREAK03_M", "BREAK03_L", "BREAK03_VL",
                "HUB0_H", "HUB0_M", "HUB0_L", "HUB0_VL",
                "HUB1_H", "HUB1_M", "HUB1_L", "HUB1_VL",
                "HUB2_H", "HUB2_M", "HUB2_L", "HUB2_VL",
                "HUB3_H", "HUB3_M", "HUB3_L", "HUB3_VL",
                "TRAILER_HITCH_H", "TRAILER_HITCH_M", "TRAILER_HITCH_L", "TRAILER_HITCH_VL",
                "SRN0_H", "SRN0_M", "SRN0_L", "SRN0_VL",
                "SRN1_H", "SRN1_M", "SRN1_L", "SRN1_VL",
                "SRN2_H", "SRN2_M", "SRN2_L", "SRN2_VL",
                "SRN3_H", "SRN3_M", "SRN3_L", "SRN3_VL",
                "HEADLIGHT0_H", "HEADLIGHT0_M", "HEADLIGHT0_L", "HEADLIGHT0_VL",
                "HEADLIGHT1_H", "HEADLIGHT1_M", "HEADLIGHT1_L", "HEADLIGHT1_VL",
                "FNDR0_H", "FNDR0_M", "FNDR0_L", "FNDR0_VL",
                "FNDR1_H", "FNDR1_M", "FNDR1_L", "FNDR1_VL",
                "WHL4_H", "WHL4_M", "WHL4_L", "WHL4_VL",
                "WHL5_H", "WHL5_M", "WHL5_L", "WHL5_VL"]

# Vehicle dashboards
dash_list = ["DAMAGE_NEEDLE_H", "DAMAGE_NEEDLE_M", "DAMAGE_NEEDLE_L", "DAMAGE_NEEDLE_VL",
             "DASH_H", "DASH_M", "DASH_L", "DASH_VL",
             "GEAR_INDICATOR_H", "GEAR_INDICATOR_M", "GEAR_INDICATOR_L", "GEAR_INDICATOR_VL",
             "ROOF_H", "ROOF_M", "ROOF_L", "ROOF_VL",
             "SPEED_NEEDLE_H", "SPEED_NEEDLE_M", "SPEED_NEEDLE_L", "SPEED_NEEDLE_VL",
             "TACH_NEEDLE_H", "TACH_NEEDLE_M", "TACH_NEEDLE_L", "TACH_NEEDLE_VL",
             "WHEEL_H", "WHEEL_M", "WHEEL_L", "WHEEL_VL", 
             "DASH_EXTRA_H", "DASH_EXTRA_M", "DASH_EXTRA_L", "DASH_EXTRA_VL"]

# Vehicle trailers
trailer_list = ["TRAILER_H", "TRAILER_M", "TRAILER_L", "TRAILER_VL",
                "SHADOW_H", "SHADOW_M", "SHADOW_L", "SHADOW_VL",
                "TLIGHT_H", "TLIGHT_M", "TLIGHT_L", "TLIGHT_VL",
                "TWHL0_H", "TWHL0_M", "TWHL0_L", "TWHL0_VL",
                "TWHL1_H", "TWHL1_M", "TWHL1_L", "TWHL1_VL",
                "TWHL2_H", "TWHL2_M", "TWHL2_L", "TWHL2_VL",
                "TWHL3_H", "TWHL3_M", "TWHL3_L", "TWHL3_VL",
                "TRAILER_HITCH_H", "TRAILER_HITCH_M", "TRAILER_HITCH_L", "TRAILER_HITCH_VL",
                "RLIGHT_H", "RLIGHT_M", "RLIGHT_L", "RLIGHT_VL",
                "BLIGHT_H", "BLIGHT_M", "BLIGHT_L", "BLIGHT_VL"]

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

# Do not export list
dne_list = ["BOUND", "BINARY_BOUND",
            "EXHAUST0_H", "EXHAUST0_M", "EXHAUST0_L", "EXHAUST0_VL",
            "EXHAUST1_H", "EXHAUST1_M", "EXHAUST1_L", "EXHAUST1_VL"]

misc_mtx_objects = ["EXHAUST0", "EXHAUST1"]

######################################################
# EXPORT HELPERS
######################################################
def reorder_objects(lst, pred):
    return_list = [None] * len(pred)
    append_list = []
    for v in lst:
        try:
            # found in list, add in it's proper order
            return_list[pred.index(v.name.upper())] = v
        except:
            # not found in predicate list, add on to the end
            append_list.append(v)
    return [x for x in return_list if x is not None] + append_list


######################################################
# EXPORT MAIN FILES
######################################################
def export_xrefs(file, selected_only):
    # build list of xrefs to export
    xref_objects = []
    for obj in bpy.context.scene.objects:
        if obj.name.lower().startswith("xref:"):
            if (selected_only and obj in bpy.context.selected_objects) or not selected_only:
                xref_objects.append(obj)

    # export xrefs
    if len(xref_objects) > 0:
        bin.write_file_header(file, "xrefs")
        num_xrefs = 0
        xref_num_offset = file.tell()
        file.write(struct.pack('L', 0))
        for obj in xref_objects:
            num_xrefs += 1
            #write matrix
            bin.write_matrix3x4(file, obj.matrix_basis)
           
            # write xref name
            xref_name = helper.get_undupe_name(obj.name[5:]) + "\x00max"
            null_length = 32 - len(xref_name)
            
            file.write(bytes(xref_name, 'utf-8'))
            file.write(bytes('\x00' * null_length, 'utf-8'))
                
        file_length = file.tell() - xref_num_offset
        file.seek(xref_num_offset - 4, 0)
        file.write(struct.pack('LL', file_length, num_xrefs))
        file.seek(0, 2)


def export_offset(file):
    bin.write_file_header(file, "offset", 12)
    file.write(struct.pack('fff', 0, 0, 0))


def export_shaders(file, context, type="byte"):
    # get our tool
    scene = context.scene
    angel = scene.angel
    
    variants = angel.variants
    num_variants = len(variants)
    write_dummy_variant = False
    
    if num_variants == 0:
        # Write a 'dummy' variant, created with the used materials
        write_dummy_variant = True
        num_variants = 1
    
    # write file header and record offset
    bin.write_file_header(file, "shaders")
    shaders_data_offset = file.tell()
    
    # prepare shaders header
    shadertype_raw = num_variants
    if type == "byte":
        shadertype_raw += 128
    shaders_per_paintjob = len(material_remap_table)
    
    # write header
    file.write(struct.pack('LL', shadertype_raw, shaders_per_paintjob))
    
    # write material sets
    ordered_material_remap = sorted(material_remap_table.items(), key =lambda x: x[1])
    if write_dummy_variant:
        # write out a variant generated on the fly with the material remap
        for material_kvp in ordered_material_remap:
            material_id = material_kvp[0]
            material = bpy.data.materials[material_id]
            
            # create a shader for it, and write it
            shader = export_helper.create_shader_from_material(material)
            shader.write(file, type)
    else:
        # write out user created variants
        for variant in variants:
            for material_kvp in ordered_material_remap:
                material_id = material_kvp[0]
                material = bpy.data.materials[material_id]
                
                # find this material in the variant
                for vm in variant.materials:
                    if vm.material.cloned_from is not None and vm.material.cloned_from == material:
                        material = vm.material
                        break
                
                # create a shader for it, and write it
                shader = export_helper.create_shader_from_material(material)
                shader.write(file, type)

    # write file length
    shaders_file_length = file.tell() - shaders_data_offset
    file.seek(shaders_data_offset - 4)
    file.write(struct.pack('L', shaders_file_length))
    file.seek(0, 2)


def export_geometry(file, meshlist, options):
    for obj in meshlist:
        # write FILE header for mesh name
        bin.write_file_header(file, helper.get_undupe_name(obj.name))
        file_data_start_offset = file.tell()
        
        # don't multiply vertices for objects requring a matrix3x4 export
        premultiply_vertices = not helper.is_matrix_object(obj)
        
        # create temp mesh
        temp_mesh = None
        if "MODIFIERS" in options:
            dg = bpy.context.evaluated_depsgraph_get()
            eval_obj = obj.evaluated_get(dg)
            temp_mesh = eval_obj.to_mesh()
        else:
            temp_mesh = obj.to_mesh()
    
        # get bmesh
        bm = bmesh.new()
        bm.from_mesh(temp_mesh)
        bm_tris = bm.calc_loop_triangles()
        
        # get mesh infos
        export_mats = export_helper.get_used_materials(obj, "MODIFIERS" in options)
        total_verts = len(bm.verts)
        total_faces = int(len(bm_tris) * 3)
        num_sections = len(export_mats)
        
        # debug
        #print("Exporting object "  + str(obj.name) + ". total_verts=" + str(total_verts) + ", total_faces=" + str(total_faces) +", num_sections=" + str(num_sections))
        
        #build FVF
        FVF_FLAGS = FVF(("D3DFVF_XYZ", "D3DFVF_NORMAL", "D3DFVF_TEX1"))
        for mat in obj.data.materials:
            if mat is not None and export_helper.is_mat_shadeless(mat):
                # undo the previous flag since we arent
                # going to write normals
                FVF_FLAGS.clear_flag("D3DFVF_NORMAL")
                break
        if "VC_DIFFUSE" in options:
            FVF_FLAGS.set_flag("D3DFVF_DIFFUSE")
        if "VC_SPECULAR" in options:
            FVF_FLAGS.set_flag("D3DFVF_SPECULAR")

        # do we need a matrix file? Only for H object
        if ((obj.location[0] != 0 or obj.location[1] != 0 or obj.location[2] != 0) and obj.name.upper().endswith("_H")):
            export_helper.write_matrix(obj.name, obj, pkg_path)

        # write mesh data header
        file.write(struct.pack('LLLLL', num_sections, total_verts, total_faces, num_sections, FVF_FLAGS.value))

        # write sections
        cur_material_index = -1
        for material in obj.data.materials:
            # get non cloned material
            real_material = material
            if material.cloned_from is not None:
                real_material = material.cloned_from
            
            # are we exporting this material?
            cur_material_index += 1
            if not real_material in export_mats:
              continue
        
            # build the mesh data we need
            cmtl_indices, cmtl_verts, cmtl_uvs, cmtl_cols = export_helper.prepare_mesh_data(bm, cur_material_index, bm_tris)

            # mesh remap done. we will now write our strip
            num_strips = 1
            section_flags = 0
            shader_offset = material_remap_table[real_material.name]
            
            # write strip to file
            file.write(struct.pack('HHL', num_strips, section_flags, shader_offset))
            strip_primType = 3
            strip_vertices = len(cmtl_verts)
            file.write(struct.pack('LL', strip_primType, strip_vertices))
            
            # write vertices
            for cv in range(len(cmtl_verts)):
                export_vert = cmtl_verts[cv]
                export_vert_location = ((obj.matrix_world @ export_vert.co) - obj.location) if premultiply_vertices else export_vert.co
                bin.write_float3(file, helper.convert_vecspace_to_mm2(export_vert_location))
                if FVF_FLAGS.has_flag("D3DFVF_NORMAL"):
                    bin.write_float3(file, helper.convert_vecspace_to_mm2(export_vert.normal))
                if FVF_FLAGS.has_flag("D3DFVF_DIFFUSE"):
                    bin.write_color4d(file, cmtl_cols[cv])
                if FVF_FLAGS.has_flag("D3DFVF_SPECULAR"):
                    bin.write_color4d(file, cmtl_cols[cv])
                uv_data = cmtl_uvs[cv]
                bin.write_float2(file, (uv_data[0], (uv_data[1] - 1) * -1))
            
            # write indices
            strip_indices_len = int(len(cmtl_indices) * 3)
            file.write(struct.pack('L', strip_indices_len))
            for ply in cmtl_indices:
                file.write(struct.pack('HHH', ply[0], ply[1], ply[2]))
        
        # clean up temp_mesh
        bm.free()
		
        # write FILE length
        file_data_length = file.tell() - file_data_start_offset
        file.seek(file_data_start_offset - 4)
        file.write(struct.pack('L', file_data_length))
        file.seek(0, 2)


def export_misc_mtx():
    for mtx in misc_mtx_objects:
        ob = bpy.data.objects.get(mtx)
        if ob is not None:
            export_helper.write_matrix(ob.name, ob, pkg_path)
    
######################################################
# EXPORT
######################################################
def save_pkg(filepath,
             e_vertexcolors,
             e_vertexcolors_s,
             apply_modifiers,
             selection_only,
             context):
    global pkg_path
    pkg_path = filepath

    print("exporting PKG: %r..." % (filepath))
    
    time1 = time.clock()
    file = open(filepath, 'wb')
    
    # create our options list
    export_options = []
    if e_vertexcolors:
        export_options.append("VC_DIFFUSE")
    if e_vertexcolors_s:
        export_options.append("VC_SPECULAR")
    if apply_modifiers:
        export_options.append("MODIFIERS")
        
    # what are we exporting?
    export_objects = None
    if selection_only:
      export_objects = bpy.context.selected_objects
    else:
      export_objects = bpy.context.scene.objects
    
      
    # first we need to figure out the export type before anything
    export_pred = generic_list
    export_typestr = 'generic'
    export_shadertype = 'byte'
    for obj in export_objects:
        if obj.type == 'MESH':
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
    
    # next we need to prepare our material list
    global material_remap_table
    material_remap_table = export_helper.create_material_remap(apply_modifiers)
    
    # finally we need to prepare our geometry list
    export_geomlist = []
    for obj in export_objects:
        if (obj.type == 'MESH' and not obj.name.upper() in dne_list):
            export_geomlist.append(obj)

    # TODO: What do we do here now??
    # special case for dashboards, if no variants are specified, it crashes
    # so we'll make defaults here
    #variants = paintjobs
    #if export_typestr == 'dash':
    #  if not "|" in paintjobs or not "," in paintjobs or not paintjobs.strip():
    #    variants = '"R",N|"R",one|"R",two|"R",three|"R",four|"R",five|"R",six'
    
    # begin write pkg file
    file.write(bytes('PKG3', 'utf-8'))
    print('\t[%.4f] exporting mesh data' % (time.clock() - time1))
    export_geometry(file, reorder_objects(export_geomlist, export_pred), export_options)
    print('\t[%.4f] exporting shaders' % (time.clock() - time1))
    export_shaders(file, context, export_shadertype)
    print('\t[%.4f] exporting xrefs' % (time.clock() - time1))
    export_xrefs(file, selection_only)
    print('\t[%.4f] exporting offset' % (time.clock() - time1))
    export_offset(file)
    print('\t[%.4f] exporting misc mtx' % (time.clock() - time1))
    export_misc_mtx()
    # end write pkg file
    print(" done in %.4f sec." % (time.clock() - time1))
    file.close()


def save(operator,
         context,
         filepath="",
         e_vertexcolors=False,
         e_vertexcolors_s=False,
         apply_modifiers=False,
         selection_only=False
         ):
    
    # save PKG
    save_pkg(filepath,
             e_vertexcolors,
             e_vertexcolors_s,
             apply_modifiers,
             selection_only,
             context,
             )

    return {'FINISHED'}
