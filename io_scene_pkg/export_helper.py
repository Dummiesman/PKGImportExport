# ##### BEGIN LICENSE BLOCK #####
#
# This program is licensed under Creative Commons BY-NC-SA:
# https://creativecommons.org/licenses/by-nc-sa/3.0/
#
# Created by Dummiesman, 2016-2020
#
# ##### END LICENSE BLOCK #####

import bpy, bmesh
import struct

from io_scene_pkg.shader_set import (ShaderSet, Shader)
import io_scene_pkg.common_helpers as helper
import io_scene_pkg.binary_helper as bin

def get_undupe_name(name):
    nidx = name.find('.')
    return name[:nidx] if nidx != -1 else name
    
def is_mat_shadeless(mat):
    for node in mat.node_tree.nodes:
        if node.type == "EMISSION":
            return True
    return False
            
def create_shader_from_material(mat):
    # get principled node
    root_node = None
    for node in mat.node_tree.nodes:
        if node.type == "BSDF_PRINCIPLED" or node.type == "EMISSION":
            root_node = node
            break
        
    if root_node is None:
        print("No Principled node. We can't export this")
        return None
    
    # create shader
    shader = Shader()
    
    color_input_name = "Base Color" if root_node.type == "BSDF_PRINCIPLED" else "Color"
    diffuse_input = root_node.inputs[color_input_name]
    if len(diffuse_input.links) > 0:
        color_input_node = diffuse_input.links[0].from_node
        if color_input_node.type == "MIX_RGB":
            # we directly have a (hopefully multiply) MIX_RGB input
            for inp in color_input_node.inputs:
                # search for color
                if len(inp.links) == 0 and inp.name != "Fac":
                    shader.diffuse_color = [inp.default_value[0], inp.default_value[1], inp.default_value[2], 1.0]
                # search for image name
                if len(inp.links) == 1:
                    image_node = inp.links[0].from_node
                    if image_node.type == "TEX_IMAGE":
                        if image_node.image is not None:
                            shader.name = get_undupe_name(image_node.image.name)
        elif color_input_node.type == "TEX_IMAGE":
            # we directly have a texture input
            if color_input_node.image is not None:
                shader.name = get_undupe_name(color_input_node.image.name)
        else:
            print("Unsupported diffuse link type. Using default value for diffuse_color.")
    else:
        shader.diffuse_color = [diffuse_input.default_value[0], diffuse_input.default_value[1], diffuse_input.default_value[2], 1.0]
    
    # assign alpha
    if root_node.type == "BSDF_PRINCIPLED":
        alpha_input = root_node.inputs["Alpha"]
        if len(alpha_input.links) > 0:
            math_node = alpha_input.links[0].from_node
            if math_node.type == "MATH":
                # we do range(2) here because there's a 3rd input we want to totally ignore
                for inp_id in range(2):
                    inp = math_node.inputs[inp_id]
                    if len(inp.links) == 0 and inp.name != "Fac":
                        shader.diffuse_color[3] = inp.default_value
            else:
                print("Unsupported alpha link type. Using default value for diffuse_color.")
        else:
            shader.diffuse_color[3] = alpha_input.default_value
    
    # assign emission
    if root_node.type == "BSDF_PRINCIPLED":
        emission_input = root_node.inputs["Emission"]
        if len(emission_input.links) > 0:
            mix_node = emission_input.links[0].from_node
            if mix_node.type == "MIX_RGB":
                for inp in mix_node.inputs:
                    if len(inp.links) == 0 and inp.name != "Fac":
                        shader.emission_color = [inp.default_value[0], inp.default_value[1], inp.default_value[2], 1.0]
            else:
                print("Unsupported diffuse link type. Using default value for diffuse_color.")
        else:
            shader.emission_color = [emission_input.default_value[0], emission_input.default_value[1], emission_input.default_value[2], 1.0]
        
    # force alpha if materials blend mode isn't set right
    if mat.blend_method == 'OPAQUE':
        shader.diffuse_color[3] = 1.0
        
    # assign shininess
    shader.shininess = root_node.inputs["Specular"].default_value

    # copy diffuse
    shader.ambient_color = shader.diffuse_color 
    
    # finally, return it
    #print("Created shader for " + mat.name)
    #shader.print()
    
    return shader
    
def get_used_materials(ob, modifiers):
    """search for used materials at object level"""
    used_materials = []
    checked_material_indices = {}
    
    # create temp mesh
    temp_mesh = None
    if modifiers:
        dg = bpy.context.evaluated_depsgraph_get()
        eval_obj = ob.evaluated_get(dg)
        temp_mesh = eval_obj.to_mesh()
    else:
        temp_mesh = ob.to_mesh()
    
    # get bmesh
    bm = bmesh.new()
    bm.from_mesh(temp_mesh)
    
    # look for used materials
    for f in bm.faces:
      if (not f.material_index in checked_material_indices 
          and f.material_index >= 0 and f.material_index < len(ob.data.materials) 
          and ob.data.materials[f.material_index] is not None):

        material = ob.data.materials[f.material_index]
        if material.cloned_from is not None: # we want the reference to the ORIGINAL
            material = material.cloned_from
        used_materials.append(material)
        checked_material_indices[f.material_index] = True
    
    # finish off
    bm.free()
    
    return used_materials

def create_material_remap(modifiers):
    all_used_mats = []
    for ob in bpy.context.scene.objects:
        if ob.type != 'MESH':
            continue
        
        used_mats = get_used_materials(ob, modifiers)
        for mat in used_mats:
            if not mat in all_used_mats:
                all_used_mats.append(mat)
     
    material_map = {}
    material_idx = 0
    for mtl in all_used_mats:
        material_map[mtl.name] = material_idx
        material_idx += 1
    return material_map
 
def bounds(obj):
    """get the bounds of an object"""
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

def write_matrix_standard(object, file):
    bnds = bounds(object)
    file.write(struct.pack('ffffffffffff', bnds.x.min,
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
                                           
def write_matrix(meshname, object, pkg_path):
    """write a *.mtx file"""
    mesh_name_parsed = helper.get_raw_object_name(meshname)
    mtx_path = pkg_path[:-4] + '_' + mesh_name_parsed + ".mtx"

    mtxfile = open(mtx_path, 'wb')
    
    if helper.is_matrix_object(object):
        bin.write_matrix3x4(mtxfile, object.matrix_world)
    else:
        write_matrix_standard(object, mtxfile)

    mtxfile.close()
    return

    
def prepare_mesh_data(mesh, material_index, tessface):
  """build mesh data for a PKG file"""
  # initialize lists for conversion
  cmtl_tris = []
  cmtl_indices = []
  cmtl_verts = []
  cmtl_uvs = []
  cmtl_cols = []
  
  # build the mesh data we need
  uv_layer = mesh.loops.layers.uv.active
  vc_layer = mesh.loops.layers.color.active

  # build tris that are in this material pass
  for lt in tessface:
      if lt[0].face.material_index == material_index:
        cmtl_tris.append(lt)

  # convert per face to per vertex indices
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
  
  # return mesh data :)
  return (cmtl_indices, cmtl_verts, cmtl_uvs, cmtl_cols)
  