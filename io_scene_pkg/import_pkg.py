# ##### BEGIN LICENSE BLOCK #####
#
# This program is licensed under Creative Commons BY-NC-SA:
# https://creativecommons.org/licenses/by-nc-sa/3.0/
#
# Created by Dummiesman, 2016-2020
#
# ##### END LICENSE BLOCK #####

import bpy, bmesh, mathutils
import os, time, struct, math

import os.path as path
from mathutils import*
from io_scene_pkg.fvf import FVF
from io_scene_pkg.shader_set import (ShaderSet, Shader)

import io_scene_pkg.binary_helper as bin
import io_scene_pkg.import_helper as import_helper
import io_scene_pkg.common_helpers as helper

pkg_path = None

######################################################
# GLOBAL LISTS
######################################################

# Misc MTX objects are objects that aren't part of PKG, but 
# related/essential enough that we load them in for user editing.
misc_mtx_objects = ["EXHAUST0", "EXHAUST1"]

######################################################
# IMPORT MAIN FILES
######################################################
def read_shaders_file(file, length, offset, import_variants):
    # get custom stuff
    scene = bpy.context.scene
    angel = scene.angel
    
    # read shader set
    shader_set = ShaderSet(file)
    
    num_variants = len(shader_set.variants)
    if num_variants <= 0:
        return
        
    num_shaders_per_variant = len(shader_set.variants[0])
    
    # setup base material set
    base_material_set = []
    base_variant = shader_set.variants[0]
    for shader_num in range(num_shaders_per_variant):
        shader = base_variant[shader_num]
        
        mtl = bpy.data.materials.get(str(shader_num))
        if mtl is not None:
            import_helper.populate_material(mtl, shader, pkg_path)
            base_material_set.append(mtl)
        else:
            base_material_set.append(None) # SHOULD NOT HAPPEN!
    
    # don't set up variants if the import flag isn't set 
    if not import_variants:
        return
        
    # clear existing variant stuff
    angel.clear()
    
    # find what materials are equal across the board
    # this will give us the ability of quickly checking if variants are unique
    # but also a reference point for variant 0
    variant_similarities = [0] * num_shaders_per_variant
    for i in range(num_variants - 1, 0, -1):
        variant_ref = shader_set.variants[i]
        variant_prev = shader_set.variants[i-1]
        for j in range(num_shaders_per_variant):
            if variant_ref[j] == variant_prev[j]:
                variant_similarities[j] += 1
   
    # setup variants
    for variant_num  in range(num_variants):
        tool_variant = angel.variants.add() # add to our tool
        variant = shader_set.variants[variant_num]
        for shader_num in range(num_shaders_per_variant):
            shader = variant[shader_num]
            
            # check if this shader is unique to this variant
            if variant_similarities[shader_num] == num_variants - 1:
                continue
            elif variant_num > 0 and shader == base_variant[shader_num]:
                continue

            # get shader base material
            base_mtl = base_material_set[shader_num]
            
            # add the base material to the variant, returning the cloned, variant version
            variant_material = tool_variant.add_material(base_mtl)
            
            # adjust the cloned version
            import_helper.populate_material(variant_material.material, shader, pkg_path)
            variant_material.material.name = helper.get_undupe_name(variant_material.material.name) + "_VARIANT" + str(variant_num)
            
    # apply it 
    angel.apply_to_scene()
    angel.selected_variant = 0
    
    # skip to the end of this FILE
    file.seek(length - (file.tell() - offset), 1)
    return


def read_xrefs(file):
    scn = bpy.context.scene

    # read xrefs
    num_xrefs = struct.unpack('<L', file.read(4))[0]
    for num in range(num_xrefs):
        # read matrix
        mtx = bin.read_matrix3x4(file)

        # read in xref name, and remove junk Angel Studios didn't null
        xref_name_bytes = bytearray(file.read(32))
        for b in range(len(xref_name_bytes)):
          if xref_name_bytes[b] > 126:
            xref_name_bytes[b] = 0
        
        # setup object
        xref_name = xref_name_bytes.decode("utf-8")
        ob = bpy.data.objects.new("xref:" + xref_name, None)
        
        # set matrix
        ob.matrix_basis = mtx
        
        ob.show_name = True
        ob.show_axis = True
        scn.collection.objects.link(ob)


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
    vc_layer = bm.loops.layers.color.new()
    
    # link to scene
    scn.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT', toggle=False)
    
    # read geometry FILE data
    num_sections, num_vertices_tot, num_indices_tot, num_sections_dupe, fvf = struct.unpack('<5L', file.read(20))
    FVF_FLAGS = FVF(fvf)

    # mesh data holders
    ob_current_material = -1

    vertex_remap_table = {}
    vertex_index_remap = {}
    mesh_vertices = []
    mesh_uvs = []
    mesh_colors = []
    
    index_offset = 0
    
    # read sections
    for num in range(num_sections):
        num_strips, strip_flags = struct.unpack('<HH', file.read(4))
        
        # check section strip flag
        FLAG_compact_strips = ((strip_flags & (1 << 8)) != 0)

        # get material, and add it to the objects material list
        shader_offset = struct.unpack('<H', file.read(2))[0] if FLAG_compact_strips else struct.unpack('<L', file.read(4))[0]
        
        # do we have this material?
        if bpy.data.materials.get(str(shader_offset)) is None:
            # we must make it!
            bpy.data.materials.new(name=str(shader_offset))
        
        ob.data.materials.append(bpy.data.materials.get(str(shader_offset)))
        ob_current_material += 1
        
        # read strips
        for strip in range(num_strips):
            # read
            prim_type = struct.unpack('<H', file.read(2))[0] if FLAG_compact_strips else struct.unpack('<L', file.read(4))[0] # seek past primtype
            num_vertices =  struct.unpack('<H', file.read(2))[0] if FLAG_compact_strips else struct.unpack('<L', file.read(4))[0]

            # read vertices
            for i in range(num_vertices):
                # read in raw data
                vpos = bin.read_float3(file)
                vnorm, vuv, vcolor = import_helper.read_vertex_data(file, FVF_FLAGS, FLAG_compact_strips)
               
                # convert coordinate spaces
                age_norm = helper.convert_vecspace_to_blender(vnorm)
                age_vert = helper.convert_vecspace_to_blender(vpos)
                age_uv = (vuv[0], (vuv[1] * -1) + 1)
                
                # add to uvs and colors list
                mesh_uvs.append(age_uv)
                mesh_colors.append(vcolor)
                
                # add vertex to mesh or remap
                pos_hash = str(age_vert)
                nrm_hash = str(age_norm)
                vertex_hash = pos_hash + "|" + nrm_hash
                
                if vertex_hash in vertex_remap_table:
                    vertex_index_remap[i+index_offset] = vertex_remap_table[vertex_hash]
                else:
                    # add vertex to mesh
                    bmvert = bm.verts.new(age_vert)
                    bmvert.normal = age_norm
               
                    vertex_remap_table[vertex_hash] = len(mesh_vertices)
                    vertex_index_remap[i+index_offset] = len(mesh_vertices)
                    
                    mesh_vertices.append(bmvert)
                    
                    
            # read indices and build mesh
            num_indices = struct.unpack('<H', file.read(2))[0] if FLAG_compact_strips else struct.unpack('<L', file.read(4))[0]

            triangle_data = None
            if FLAG_compact_strips and prim_type == 4:
             tristrip_data = struct.unpack('<' + str(num_indices) + 'H', file.read(2 * num_indices))
             triangle_data = import_helper.convert_triangle_strips(tristrip_data)
            else:
             triangle_data = struct.unpack('<' + str(num_indices) + 'H', file.read(2 * num_indices))

            for i in range(0, len(triangle_data), 3):
              tri_indices = triangle_data[i:i+3]
              try:
                  # get verts
                  v0 = mesh_vertices[vertex_index_remap[tri_indices[0]+index_offset]]
                  v1 = mesh_vertices[vertex_index_remap[tri_indices[1]+index_offset]]
                  v2 = mesh_vertices[vertex_index_remap[tri_indices[2]+index_offset]]
                  
                  # setup face
                  face = bm.faces.new((v0, v1, v2))
                  face.smooth = True
                  face.material_index = ob_current_material
                  
                  # set uvs
                  for uv_set_loop in range(3):
                    face.loops[uv_set_loop][uv_layer].uv = mesh_uvs[tri_indices[uv_set_loop] + index_offset]
                    
                  # set colors
                  if FVF_FLAGS.has_flag("D3DFVF_DIFFUSE") or FVF_FLAGS.has_flag("D3DFVF_SPECULAR"):
                      for color_set_loop in range(3):
                        face.loops[color_set_loop][vc_layer] = mesh_colors[tri_indices[color_set_loop] + index_offset]
                    
              except Exception as e:
                  print(str(e))
            
            index_offset += num_vertices

    # apply bmesh data to object
    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    bm.to_mesh(me)
    bm.free()
    
    # calculate normals
    if FVF_FLAGS.has_flag("D3DFVF_NORMAL"):
      me.calc_normals()

    # lastly, look for a MTX file. Don't grab an MTX for FNDR_M/L/VL though
    # as the FNDR lods are static and don't use the mtx
    if not ("fndr" in meshname.lower() and not "_h" in meshname.lower()):
      if helper.is_matrix_object(ob):
        # some objects actually use MTX as a matrix.
        mtx = import_helper.find_matrix3x4(meshname, pkg_path)
        if mtx is not None:
            ob.matrix_world = mtx
      else:
        # others use it as min,max,pivot,origin
        found, min, max, pivot, origin = import_helper.find_matrix(meshname, pkg_path)
        if found:
            ob.location = origin
          
    return

def import_misc_mtx():
    scn = bpy.context.scene
    for mtx in misc_mtx_objects:
        found, min, max, pivot, origin = import_helper.find_matrix(mtx, pkg_path)
        if found:
            ob = bpy.data.objects.new(mtx, None)
            ob.location = origin
            ob.empty_display_size = 0.5
            ob.show_name = True
            scn.collection.objects.link(ob)
        
######################################################
# IMPORT
######################################################
def load_pkg(filepath,
             context,
             import_variants=True):
    # set the PKG path, used for finding textures
    global pkg_path
    pkg_path = filepath

    # start import
    print("importing PKG: %r..." % (filepath))

    if bpy.ops.object.select_all.poll():
        bpy.ops.object.select_all(action='DESELECT')

    time1 = time.perf_counter()
    file = open(filepath, 'rb')

    # start reading our pkg file
    pkg_version = file.read(4).decode("utf-8")
    if pkg_version != "PKG3" and pkg_version != "PKG2":
        print('\tFatal Error: PKG file is wrong format : ' + pkg_version)
        file.close()
        return
        
    pkg_version_id = int(pkg_version[-1:])

    # read pkg FILE's
    pkg_size = path.getsize(filepath)
    while file.tell() != pkg_size:
        file_header = None
        try:
          file_header = file.read(4).decode("utf-8")
        except Exception as e:
          print("cannot decode file header @ " + str(file.tell()))
          print(str(e))
          file.close()
          raise

        # check for an invalid header
        if file_header != "FILE":
            print('\tFatal Error: PKG file is corrupt, missing FILE header at ' + str(file.tell()))
            file.close()
            return

        # found a proper FILE header
        file_name = bin.read_angel_string(file)
        file_length = 0 if pkg_version_id == 2 else struct.unpack('<L', file.read(4))[0]
        
        # Angel released a very small batch of corrupt PKG files
        # this is here just in case someone tries to import one
        if file_length == 0 and pkg_version_id == 3:
            print("Invalid PKG3 file : cannot have file length of 0")
            file.close()
            return
            
        print('\t[' + str(round(time.perf_counter() - time1, 3)) + '] processing : ' + file_name)
        if file_name == "shaders":
            # load shaders file
            read_shaders_file(file, file_length, file.tell(), import_variants)
        elif file_name == "offset":
            # skip over this, seems it's meta
            if pkg_version_id == 3:
               file.seek(file_length, 1)
            else:
              file.seek(12, 1)
        elif file_name == "xrefs":
            read_xrefs(file)
        else:
            # assume geometry
            read_geometry_file(file, file_name)
    # END READ PKG FILE DATA
    
    # READ MISC MTX
    import_misc_mtx()
    # END READ MISC MTX
    
    print(" done in %.4f sec." % (time.perf_counter() - time1))
    file.close()


def load(operator,
         context,
         filepath="",
         import_variants=True
         ):
         
    load_pkg(filepath,
             context,
             import_variants
             )

    return {'FINISHED'}
