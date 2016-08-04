# ##### BEGIN LICENSE BLOCK #####
#
# This program is licensed under Creative Commons BY-NC-SA:
# https://creativecommons.org/licenses/by-nc-sa/3.0/
#
# Copyright (C) Dummiesman, 2016
#
# ##### END LICENSE BLOCK #####
import bpy, bmesh

def get_material_offset(mtl):
    # :( hack
    coffset = 0
    for mat in bpy.data.materials:
        if mtl.name == mat.name:
            return coffset
        coffset += 1
    return -1


    
def get_used_materials(ob, modifiers):
  used_materials = []
  
  # create temp mesh
  temp_mesh = ob.to_mesh(bpy.context.scene, modifiers, 'PREVIEW')
  
  # get bmesh
  bm = bmesh.new()
  bm.from_mesh(temp_mesh)
  
  # look for used materials
  for f in bm.faces:
    if not f.material_index in used_materials and f.material_index >= 0 and ob.material_slots[f.material_index].material is not None:
      used_materials.append(f.material_index)
  
  # finish off
  bpy.data.meshes.remove(temp_mesh)
  bm.free()
  
  return used_materials
  
def prepare_materials(modifiers):
  material_list =[]
  material_idx_list = []
  material_reorder = {}
  
  # prepare mat list
  for ob in bpy.data.objects:
    if ob.type == 'MESH' and len(ob.material_slots) > 0:
      # get idx's of used mats (local)
      idx_list = get_used_materials(ob, modifiers)
      
      # remap to global
      for x in range(len(idx_list)):
        idx_list[x] = get_material_offset(ob.material_slots[idx_list[x]].material)
        
      material_idx_list.extend(idx_list)
  
  material_idx_list.sort()
  
  # prepare remap dict & material list
  for x in range(len(material_idx_list)):
    # remap
    cidx = material_idx_list[x]
    if not cidx in material_reorder and cidx >= 0:
      material_reorder[cidx] = len(material_list)
      material_list.append(bpy.data.materials[cidx])
      
  return (material_list, material_reorder)
      
    
  
      
  
  