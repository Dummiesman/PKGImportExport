# ##### BEGIN LICENSE BLOCK #####
#
# This program is licensed under Creative Commons BY-NC-SA:
# https://creativecommons.org/licenses/by-nc-sa/3.0/
#
# Copyright (C) Dummiesman, 2016
#
# ##### END LICENSE BLOCK #####

import bpy, bmesh
import os, time, struct

import os.path as path

from io_scene_pkg.fvf import FVF

import io_scene_pkg.binary_helper as bin
import io_scene_pkg.export_helper as helper


# globals
global pkg_path
pkg_path = None

global apply_modifiers_G
apply_modifiers_G = True

global material_remap_table
material_remap_table = {}


######################################################
# GLOBAL LISTS
######################################################

# AI/Player Vehicle
vehicle_list = ["BODY", "SHADOW", "HLIGHT", "TLIGHT", "SLIGHT0", "SLIGHT1",
                "RLIGHT", "BLIGHT", "BODYDAMAGE", "SIREN0", "SIREN1", "DECAL",
                "DRIVER", "SHOCK0", "SHOCK1", "SHOCK2", "SHOCK3",
                "ARM0", "ARM1", "ARM2", "ARM3", "SHAFT2", "SHAFT3",
                "AXLE0", "AXLE1", "ENGINE", "WHL0", "WHL1", "WHL2", "WHL3",
                "BREAK0", "BREAK1", "BREAK2", "BREAK3", "BREAK01", "BREAK12",
                "BREAK23", "BREAK03", "HUB0", "HUB1", "HUB2", "HUB3", "TRAILER_HITCH",
                "SRN0", "SRN1", "SRN2", "SRN3", "HEADLIGHT0", "HEADLIGHT1",
                "FNDR0", "FNDR1", "WHL4", "WHL5"]

# Vehicle Dashboards
dash_list = ["DAMAGE_NEEDLE", "DASH", "GEAR_INDICATOR", "ROOF", "SPEED_NEEDLE",
             "TACH_NEEDLE", "WHEEL", "DASH_EXTRA"]

# Vehicle trailers
trailer_list = ["TRAILER_H", "TRAILER_M", "TRAILER_L", "TRAILER_VL",
                "SHADOW_H", "SHADOW_M", "SHADOW_L", "SHADOW_VL",
                "TLIGHT_H", "TLIGHT_M", "TLIGHT_L", "TLIGHT_VL",
                "TWHL0_H", "TWHL0_M", "TWHL0_L", "TWHL0_VL",
                "TWHL1_H", "TWHL1_M", "TWHL1_L", "TWHL1_VL",
                "TWHL2_H", "TWHL2_M", "TWHL2_L", "TWHL2_VL",
                "TWHL3_H", "TWHL3_M", "TWHL3_L", "TWHL3_VL",
                "TRAILER_HITCH_H", "TRAILER_HITCH_M", "TRAILER_HITCH_L", "TRAILER_HITCH_VL",
                "RLIGHT_H", "RLIGHT_M", "RLIGHT_L", "RLIGHT_VL"]

# Props, buildings, etc
generic_list = ["MAIN", "SHADOW", "MASK", "NONRANDOM", "REFL", "OPAQUE", "BREAK01", "BREAK02", "BREAK03", "BREAK04",
                "BREAK05", "BREAK06", "BREAK07", "BREAK08", "BREAK09",
                "REDGLOWDAY", "YELLOWGLOWDAY", "GREENGLOWDAY", "WALK_DAY", 
                "NOWALK_DAY", "REDGLOWNIGHT", "YELLOWGLOWNIGHT", "GREENGLOWNIGHT",
                "WALK_NIGHT", "NOWALK_NIGHT"]


# do not export' list
dne_list = ["BOUND", "BINARY_BOUND",
            "EXHAUST0", "EXHAUST1"]

######################################################
# EXPORT HELPERS
######################################################
def reorder_objects(lst, pred):
    return_list = [None] * len(pred)
    append_list = []
    for v in lst:
        try:
            #print("FOUND " + v.name)
            return_list[pred.index(v.name.upper())] = v
        except:
            # not found in predicate list
            #print(v.name + " NOT FOUND, ADDING TO END")
            append_list.append(v)
    return [x for x in return_list if x is not None] + append_list


def get_undupe_name(name):
    nidx = name.find('.')
    return name[:nidx] if nidx != -1 else name


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


def find_object_ci(name):
    for obj in bpy.data.objects:
        if obj.name.lower() == name.lower():
            return obj
    return None


def handle_replace_logic(rw1, rw2, rpd):
  # exact match mode? return replace word
  if rw1.startswith("\"") and rw1.endswith("\""):
    matchto = rw1[1:-1].lower()
    if rpd.lower() == matchto:
      return rw2
  
  # basic logic
  return rpd.replace(rw1, rw2)

######################################################
# EXPORT MAIN FILES
######################################################
def export_xrefs(file, selected_only):
    # build list of xrefs to export
    xref_objects = []
    for obj in bpy.data.objects:
        if obj.name.startswith("xref:"):
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
            xref_name = get_undupe_name(obj.name[5:]) + "\x00max"
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
    bin.write_file_header(file, "offset", 12)
    file.write(struct.pack('fff', 0, 0, 0))


def export_shaders(file, replace_words, materials, type="byte"):
    # First paintjob replace word. If this isn't added we get paintjobs-1 paintjobs :(
    replace_words.insert(0, ['$!*%&INVALIDMATERIAL&%*!$', '$!*%&INVALIDMATERIAL&%*!$'])
    # write file header and record offset
    bin.write_file_header(file, "shaders")
    shaders_data_offset = file.tell()
    # prepare shaders header
    shadertype_raw = len(replace_words)
    if type == "byte":
        shadertype_raw += 128
    shaders_per_paintjob = len(materials)
    # write header
    file.write(struct.pack('LL', shadertype_raw, shaders_per_paintjob))
    # write material sets
    for rwa in replace_words:
        # export a material set
        for mtl in materials:
            #bname = mtl.name
            
            #if mtl.active_texture is not None:
            #    bname = mtl.active_texture.name  # use texture name instead
            
            # handle material name replacement
            mtl_name = handle_replace_logic(rwa[0], rwa[1], get_undupe_name(mtl.name))
            
            if mtl_name.startswith('mm2:notexture') or mtl_name.startswith('age:notexture'):
                # matte material
                print("Material " + mtl_name + " is a matte material")
                for val in range(3):
                  print("diffuse color [" + str(val) + "]=" + str(mtl.diffuse_color[val]))
                bin.write_angel_string(file, '')
            else:
                # has texture
                bin.write_angel_string(file, mtl_name)

            # calculate alpha for writing
            mtl_alpha = 1
            mtl_emit = mtl.emit / 2.0
            mtl_emit_color = [mtl.diffuse_color[0] * mtl_emit, mtl.diffuse_color[1] * mtl_emit, mtl.diffuse_color[2] * mtl_emit]
            if mtl.use_transparency:
                mtl_alpha = mtl.alpha

              
            if type == "byte":
                bin.write_color4d(file, mtl.diffuse_color, mtl_alpha) # diffuse
                bin.write_color4d(file, mtl.diffuse_color, mtl_alpha) # ambient 
                bin.write_color4d(file, mtl_emit_color) # emissive
            elif type == "float":
                bin.write_color4f(file, mtl.diffuse_color, mtl_alpha) # diffuse
                bin.write_color4f(file, mtl.diffuse_color, mtl_alpha) # ambient
                bin.write_color4f(file, mtl.specular_color) # specular
                bin.write_color4f(file, mtl_emit_color) # emissive

            # shininess
            file.write(struct.pack('f', mtl.raytrace_mirror.reflect_factor))

    # write file length
    shaders_file_length = file.tell() - shaders_data_offset
    file.seek(shaders_data_offset - 4)
    file.write(struct.pack('L', shaders_file_length))
    file.seek(0, 2)


def export_mesh(file, name, obj, options):
      # write FILE header for mesh name
      bin.write_file_header(file, get_undupe_name(name))
      file_data_start_offset = file.tell()
      
      # create temp mesh
      temp_mesh = obj.to_mesh(bpy.context.scene, apply_modifiers_G, 'PREVIEW')
      
      # get bmesh
      bm = bmesh.new()
      bm.from_mesh(temp_mesh)
      bm_tris = bm.calc_tessface()
      
      # get mesh infos
      export_mats = helper.get_used_materials(obj, apply_modifiers_G)
      total_verts = 0
      total_indices = 0
      num_sections = len(export_mats)
      
      # prepare mesh data for export
      prepared_mesh_data = []
      for mat_slot in obj.material_slots:
        material_index = len(prepared_mesh_data)
        if not material_index in export_mats:
          prepared_mesh_data.append([])
          continue
          
        cmtl_indices, cmtl_verts, cmtl_uvs, cmtl_cols = helper.prepare_mesh_data(bm, material_index, bm_tris)
        total_verts += len(cmtl_verts)
        total_indices += len(cmtl_indices) * 3
        prepared_mesh_data.append([cmtl_indices, cmtl_verts, cmtl_uvs, cmtl_cols])
        
        
      #build FVF
      FVF_FLAGS = FVF(("D3DFVF_XYZ", "D3DFVF_NORMAL", "D3DFVF_TEX1"))
      for mat in obj.data.materials:
          if mat is not None and mat.use_shadeless:
              # undo the previous flag since we arent
              # going to write normals
              FVF_FLAGS.clear_flag("D3DFVF_NORMAL")
              break
      if "VC_DIFFUSE" in options:
          FVF_FLAGS.set_flag("D3DFVF_DIFFUSE")
      if "VC_SPECULAR" in options:
          FVF_FLAGS.set_flag("D3DFVF_SPECULAR")

      # write mesh data header
      file.write(struct.pack('LLLLL', num_sections, total_verts, total_indices, num_sections, FVF_FLAGS.value))

      # write sections
      cur_material_index = -1
      for mat_slot in obj.material_slots:
          # are we exporting this material?
          cur_material_index += 1
          if not cur_material_index in export_mats:
            continue
      
          # build the mesh data we need
          cmtl_indices, cmtl_verts, cmtl_uvs, cmtl_cols = prepared_mesh_data[cur_material_index]

          # mesh remap done. we will now write our strip
          num_strips = 1
          section_flags = 0
          shader_offset = material_remap_table[helper.get_material_offset(obj.material_slots[cur_material_index].material)]
          
          # write strip to file
          file.write(struct.pack('HHL', num_strips, section_flags, shader_offset))
          strip_primType = 3
          strip_vertices = len(cmtl_verts)
          file.write(struct.pack('LL', strip_primType, strip_vertices))
          
          # write vertices
          for cv in range(len(cmtl_verts)):
              export_vert = cmtl_verts[cv]
              export_vert_location = (obj.matrix_local * export_vert.co)
              bin.write_float3(file, (export_vert_location[0], export_vert_location[2], export_vert_location[1] * -1))
              if FVF_FLAGS.has_flag("D3DFVF_NORMAL"):
                  bin.write_float3(file, (export_vert.normal[0], export_vert.normal[2], export_vert.normal[1] * -1))
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
      bpy.data.meshes.remove(temp_mesh)
      bm.free()
  
      # write FILE length
      file_data_length = file.tell() - file_data_start_offset
      file.seek(file_data_start_offset - 4)
      file.write(struct.pack('L', file_data_length))
      file.seek(0, 2)

def export_meshes(file, meshlist, options):
    for obj in meshlist:
      lods = [None, None, None, None]
      pivot = None
      
      print("obj " + obj.name + " childcount " + str(len(obj.children)))
      # get lods
      for child in obj.children:
        lodname = get_undupe_name(child.name).lower()
        print("Searching obj " + obj.name + " child " + child.name + " undupe " + lodname)
        if lodname == "h":
          lods[0] = child
        if lodname== "m":
          lods[1] = child
        if lodname == "l":
          lods[2] = child
        if lodname == "vl":
          lods[3] = child
        if lodname == "pivot":
          pivot = child
          
      # export meshes
      if lods[0] is not None:
        export_mesh(file, "H" if obj.name.lower() == "main" else obj.name + "_H", lods[0], options)
      if lods[1] is not None:
        export_mesh(file, "M" if obj.name.lower() == "main" else obj.name + "_M", lods[1], options)
      if lods[2] is not None:
        export_mesh(file, "L" if obj.name.lower() == "main" else obj.name + "_L", lods[2], options)
      if lods[3] is not None:
        export_mesh(file, "VL" if obj.name.lower() == "main" else obj.name + "_VL", lods[3], options)
        
      # write pivot
      if (obj.location[0] != 0 or obj.location[1] != 0 or obj.location[2] != 0):
          helper.write_matrix(obj.name, obj, pivot, pkg_path)
        


######################################################
# EXPORT
######################################################
def save_pkg(filepath,
             paintjobs,
             e_vertexcolors,
             e_vertexcolors_s,
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
    
    # what are we exporting?
    export_objects = []
    potential_objects = bpy.context.selected_objects if selection_only else bpy.data.objects

    # sort through our potential objects
    for obj in potential_objects:
      ob_name = obj.name.upper()
      if obj.type == 'EMPTY' and (ob_name in vehicle_list or ob_name in generic_list or ob_name in dash_list or ob_name in trailer_list):
        export_objects.append(obj)
    
      
    # first we need to figure out the export type before anything
    export_pred = generic_list
    export_typestr = 'generic'
    export_shadertype = 'byte'
    for obj in export_objects:
      print("should export " + obj.name)
      # we can check this object :)
      if obj.name.upper() == "DASH":
          export_shadertype = 'float'
          export_typestr = 'dash'
          export_pred = dash_list
          break
      if obj.name.upper() == "BODY":
          export_typestr = 'vehicle'
          export_pred = vehicle_list
          break
      if obj.name.upper() == "TRAILER":
          export_typestr = 'trailer'
          export_pred = trailer_list
          break

    print('\tPKG autodetected export type: ' + export_typestr)
    
    # next we need to prepare our material list
    export_materials, export_material_remap = helper.prepare_materials(apply_modifiers_G)
    
    global material_remap_table
    material_remap_table = export_material_remap
    
    # special case for dashboards, if no variants are specified, it crashes
    # so we'll make defaults here
    variants = paintjobs
    if export_typestr == 'dash':
      if not "|" in paintjobs or not "," in paintjobs or not paintjobs.strip():
        variants = '"R",N|"R",one|"R",two|"R",three|"R",four|"R",five|"R",six'
    
    # WRITE PKG FILE
    file.write(bytes('PKG3', 'utf-8'))
    print('\t[%.4f] exporting mesh data' % (time.clock() - time1))
    export_meshes(file, reorder_objects(export_objects, export_pred), export_options)
    print('\t[%.4f] exporting shaders' % (time.clock() - time1))
    export_shaders(file, get_replace_words(variants), export_materials, export_shadertype)
    print('\t[%.4f] exporting xrefs' % (time.clock() - time1))
    export_xrefs(file, selection_only)
    print('\t[%.4f] exporting offset' % (time.clock() - time1))
    export_offset(file)
    # PKG WRITE DONE
    print(" done in %.4f sec." % (time.clock() - time1))
    file.close()


def save(operator,
         context,
         filepath="",
         additional_paintjobs="",
         e_vertexcolors=False,
         e_vertexcolors_s=False,
         apply_modifiers=False,
         selection_only=False
         ):
    
    
    # set globals
    global apply_modifiers_G
    apply_modifiers_G = apply_modifiers
    
    # save PKG
    save_pkg(filepath,
             additional_paintjobs,
             e_vertexcolors,
             e_vertexcolors_s,
             selection_only,
             context,
             )

    return {'FINISHED'}
