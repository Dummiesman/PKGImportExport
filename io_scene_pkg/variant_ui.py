import bpy
import re
from bpy.types import (Panel,
                       Menu,
                       Operator,
                       PropertyGroup,
                       UIList
                       )
                       
from bpy.props import (IntProperty,
                       BoolProperty,
                       StringProperty,
                       CollectionProperty,
                       PointerProperty)

# -------------------------------------------------------------------
#   Operators
# -------------------------------------------------------------------
        
class AddVariantOperator(Operator):
    bl_idname = "angel.add_variant"
    bl_label = "Add Variant"
    
    def execute(self, context):
        scene = context.scene
        angel = scene.angel
        
        is_first_variant = len(angel.variants) == 0
        variant = angel.variants.add()
        
        # clone from first
        if not is_first_variant:
            variant.clone_from(angel.get_selected_variant())
        
        angel.selected_variant = len(angel.variants) - 1
        
        return {'FINISHED'}

class DeleteVariantOperator(Operator):
    bl_idname = "angel.delete_variant"
    bl_label = "Delete Variant"
    
    def execute(self, context):
        scene = context.scene
        angel = scene.angel
        
        if angel.selected_variant < len(angel.variants):
            angel.revert_to_base_materials() # YUCK! We go through all the trouble of reverting and reassigning materials,
            
            variant = angel.variants[angel.selected_variant]
            variant.remove_all_materials()
            angel.variants.remove(angel.selected_variant)
            
            if angel.selected_variant > 0:
                angel.selected_variant -= 1
            angel.apply_to_scene()
        
        return {'FINISHED'}
        
class DeleteVariantConfirmOperator(Operator):
    """Really?"""
    bl_idname = "angel.delete_variant_confirm"
    bl_label = "Do you really want to delete this variant?"
    bl_options = {'REGISTER', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        bpy.ops.angel.delete_variant()
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)
        
class RemoveMaterialFromVariantOperator(Operator):
    bl_idname = "angel.remove_material_from_variant"
    bl_label = "Remove Material From Variant"
    
    def execute(self, context):
        scene = context.scene
        angel = scene.angel
        variant = angel.get_selected_variant()
        
        if variant.material_index < len(variant.materials):
            angel.revert_to_base_materials() # YUCK! We go through all the trouble of reverting and reassigning materials,
            
            mtl_to_remove = variant.materials[variant.material_index].material
            variant.remove_material(mtl_to_remove)
            
            variant.apply_to_scene()

        return {'FINISHED'}
        
class AddMaterialToVariantOperator(Operator):
    bl_idname = "angel.add_material_to_variant"
    bl_label = "Add Material To Variant"
    
    def execute(self, context):
        scene = context.scene
        angel = scene.angel
        
        mtl_to_add = bpy.data.materials[angel.material_pool_index]
        
        variant = angel.get_selected_variant()
        variant.add_material(mtl_to_add)
        
        variant.apply_to_scene()
        
        return {'FINISHED'}
      
# -------------------------------------------------------------------
#   Drawing
# -------------------------------------------------------------------
class ANGEL_UL_materials(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        mat = item.material
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(mat, "name", text="", emboss=False, icon_value=layout.icon(mat))
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=layout.icon(mat))

    def invoke(self, context, event):
        pass
        
class ANGEL_UL_materials_unused(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        mat = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(mat, "name", text="", emboss=False, icon_value=layout.icon(mat))
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=layout.icon(mat))

    def filter_items(self, context, data, propname):
        # get our tool
        scene = context.scene
        angel = scene.angel
        
        # get our variant materials
        variant = angel.get_selected_variant()
        variant_materials = variant.materials
        variant_materials_list = []
        
        # make a list of these, instead of a list of VariantMaterial
        for vm in variant_materials:
            variant_materials_list.append(vm.material)
        
        # Filter
        mats = getattr(data, propname)
        
        # Default return values.
        flt_flags = []
        flt_neworder = []
        
        flt_flags = [self.bitflag_filter_item] * len(mats)
        
        # Filter by emptiness.
        for idx, item in enumerate(mats):
            mat = item
            is_in_variant_cloned = False
            for vm in variant_materials_list:
                if vm.cloned_from == mat:
                    is_in_variant_cloned = True
                    break
            if mat.cloned_from is not None or mat in variant_materials_list or is_in_variant_cloned:
                flt_flags[idx] &= ~self.bitflag_filter_item

        
        return flt_flags, flt_neworder

    def invoke(self, context, event):
        pass
        
class ANGEL_PT_AngelPanel(Panel):
    bl_label = "Angel Tools"
    bl_idname = "ANGEL_PT_angel_tools_panel"
    bl_space_type = "VIEW_3D"   
    bl_region_type = "UI"
    bl_category = "Angel Tools" 


    @classmethod
    def poll(self,context):
        return True

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        angel = scene.angel
            
        layout.label(text="Variant Editor")
        layout.separator()
        
        row = layout.row()
        row.label(text=str(len(angel.variants)) + " variants")
        row.operator("angel.delete_variant_confirm", text= "-")
        row.operator("angel.add_variant", text= "+")
        
        layout.prop(angel, "selected_variant")
        selected_variant = angel.selected_variant
        
        layout.separator()
        if selected_variant >= len(angel.variants):
            layout.label(text="Selected variant has not been created yet.")
        else:
            variant = angel.variants[selected_variant]
            
            # draw used list
            layout.label(text="Materials In Variant")
        
            rows = 4
            row = layout.row()
            row.template_list("ANGEL_UL_materials", "", variant, "materials", variant, "material_index", rows=rows)
            
            # draw remove from button
            row = layout.row()
            row.operator("angel.remove_material_from_variant")
            
            # draw selected mat
            #layout.template_preview(context.active_object.active_material, show_buttons=True)
            
            # draw unused list
            layout.label(text="Materials Not In Variant (Shared)")
            layout.template_list("ANGEL_UL_materials_unused", "", bpy.data, "materials", angel, "material_pool_index", rows=rows)           
            
            # draw add to button
            row = layout.row()
            row.operator("angel.add_material_to_variant")


# -------------------------------------------------------------------
#   Register & Unregister
# -------------------------------------------------------------------

classes = (
    AddVariantOperator,
    DeleteVariantOperator,
    DeleteVariantConfirmOperator,
    AddMaterialToVariantOperator,
    RemoveMaterialFromVariantOperator,
    ANGEL_PT_AngelPanel,
    ANGEL_UL_materials,
    ANGEL_UL_materials_unused
)

def register():        
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    
def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)


    
    