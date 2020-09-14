import bpy
from bpy.props import (
        CollectionProperty,
        IntProperty,
        PointerProperty
        )

from bpy.types import (
        Material,
        PropertyGroup
        )
        
        
class VariantMaterial(PropertyGroup):
    material: PointerProperty(
        name="Material",
        type=Material
        )
    
class Variant(PropertyGroup):
    materials: CollectionProperty(
        name = "Materials",
        type = VariantMaterial
        )
    
    material_index: IntProperty()
    
    
    def apply_to_scene(self):
        for ob in bpy.data.objects:
            if ob.type != 'MESH':
                continue
            
            mtl_count = len(ob.data.materials)
            for i in range(mtl_count):
                mtl = ob.data.materials[i]
                complementing_mtl = None
                
                for vm in self.materials:
                    if vm.material.cloned_from == mtl.cloned_from or vm.material.cloned_from == mtl:
                        complementing_mtl = vm.material
                        break
                 
                if complementing_mtl is not None or mtl.cloned_from is not None:
                    ob.data.materials[i] = complementing_mtl if complementing_mtl is not None else mtl.cloned_from
            
            
    def clone_from(self, variant):
        for vm in variant.materials:
            self.add_material(vm.material)
    
    def add_material(self, material):
        # reject already added materials
        for vm in self.materials:
            if vm.material.cloned_from == material:
                return None

        # add material
        variant_material = self.materials.add()
        
        material_copy = material.copy()
        material_copy.name = material.name + "_variant"
        
        # if we're cloning a clone, use it's cloned_from
        if material.cloned_from is not None:
            material_copy.cloned_from = material.cloned_from
        else:
            material_copy.cloned_from = material
        
        variant_material.material = material_copy
        
        return variant_material
        
    def add_all_materials(self):
        for material in bpy.data.materials:
            self.add_material(material)
    
    def remove_all_materials(self):
        for vm in self.materials:
            material = vm.material
            bpy.data.materials.remove(material, do_unlink=True) # this is a cloned material, so we delete it once it's no longer used
        self.materials.clear()
        
    def remove_material(self, material):
        found_index = -1
        for idx, item in enumerate(self.materials):
            if item.material == material:
                found_index = idx
                break
        if found_index >= 0:
            material = self.materials[found_index].material
            self.materials.remove(found_index)
            bpy.data.materials.remove(material, do_unlink=True) # this is a cloned material, so we delete it once it's no longer used
        return found_index >= 0
        
    
class AngelSceneData(PropertyGroup):
    def __set_selected_variant_callback(self, num):
        self["selected_variant"] = num
        if num < 0 or num >= len(self.variants):
            return
        variant = self.variants[num]
        variant.apply_to_scene()

    def __get_selected_variant_callback(self):
        return self.get("selected_variant", 0)
        
    variants: CollectionProperty(
        name = "Variants",
        type = Variant
        )

    selected_variant: IntProperty(
        name = "Selected Variant",
        description="Currently Selected Variant",
        default = 0,
        min = 0,
        max = 32,
        get = __get_selected_variant_callback,
        set = __set_selected_variant_callback
        )
     
    # index used for "not in variant" list
    material_pool_index: IntProperty()     
    
    def apply_to_scene(self):
        variant = self.get_selected_variant()
        if variant is not None:
            variant.apply_to_scene()
    
    def revert_to_base_materials(self):
        for ob in bpy.data.objects:
            if ob.type != 'MESH':
                continue
            
            mtl_count = len(ob.data.materials)
            for i in range(mtl_count):
                mtl = ob.data.materials[i]
                original_mtl = mtl.cloned_from
                ob.data.materials[i] = original_mtl if original_mtl is not None else mtl
                    
                    
    def get_selected_variant(self):
        if self.selected_variant >= len(self.variants) or self.selected_variant < 0:
            return None
        return self.variants[self.selected_variant]
        
        
def register():
    bpy.utils.register_class(VariantMaterial)
    bpy.utils.register_class(Variant)
    bpy.utils.register_class(AngelSceneData)
    
def unregister():
    bpy.utils.unregister_class(AngelSceneData)
    bpy.utils.unregister_class(Variant)
    bpy.utils.unregister_class(VariantMaterial)
