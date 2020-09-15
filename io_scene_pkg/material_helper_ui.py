 # ##### BEGIN LICENSE BLOCK #####
#
# This program is licensed under Creative Commons BY-NC-SA:
# https://creativecommons.org/licenses/by-nc-sa/3.0/
#
# Created by Dummiesman, 2016-2020
#
# ##### END LICENSE BLOCK #####

import bpy, mathutils

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

class CreateMaterialSetupOperator(Operator):
    """Creates a full node setup that lets you set up all aspects of a PKG shader.
       Experienced users can also choose set this up manually"""
    bl_idname = "angel.create_material_setup"
    bl_label = "Create Material Setup"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}
    
    def execute(self, context):
        scene = context.scene
        
        # TODO?
        # Move most of this into common_helpers, and use it to setup a base for import_helpers
        # then assign values by getting nodes by name. Currently this is essentially just a huge
        # copy paste from import_helpers
        
        # get active material
        ob = context.active_object
        material = ob.active_material
        is_mat_modified = False
        
        # check if it's made by Blender, or touched by the user
        if len(material.node_tree.nodes) != 2:
            is_mat_modified = True
        for node in material.node_tree.nodes:
            if node.type != "BSDF_PRINCIPLED" and node.type != "OUTPUT_MATERIAL":
                is_mat_modified = True
        
        if is_mat_modified:
            self.report({'ERROR'}, "This material has been modified. This operation only works on brand new materials.")
            return {'CANCELLED'}
            
        # continuing on, we start making the node setup now
        bsdf = material.node_tree.nodes["Principled BSDF"]
        
        bsdf.inputs['Emission'].default_value = (0, 0, 0, 1)
        bsdf.inputs['Specular'].default_value = 0.0
        bsdf.inputs['Roughness'].default_value = 0
        
        # create image node
        tex_image_node = material.node_tree.nodes.new('ShaderNodeTexImage')
        tex_image_node.location = mathutils.Vector((-640.0, 20.0))
        
        # create diffuse blend node
        blend_node = material.node_tree.nodes.new('ShaderNodeMixRGB')
        blend_node.inputs['Color2'].default_value = (1, 1, 1, 1)
        blend_node.inputs['Fac'].default_value = 1.0
        blend_node.blend_type = 'MULTIPLY'
        blend_node.label = "Diffuse Color"
        blend_node.location = mathutils.Vector((-260.0, 160.0))
        
        # hook up diffuse
        material.node_tree.links.new(blend_node.inputs['Color1'], tex_image_node.outputs['Color'])
        material.node_tree.links.new(bsdf.inputs['Base Color'], blend_node.outputs['Color'])
        
        # create emissive blend node
        blend_node = material.node_tree.nodes.new('ShaderNodeMixRGB')
        blend_node.inputs['Color2'].default_value = (0, 0, 0, 1)
        blend_node.inputs['Fac'].default_value = 1.0
        blend_node.blend_type = 'MULTIPLY'
        blend_node.label = "Emission Color"
        blend_node.location = mathutils.Vector((-260.0, -20.0))
        
        material.node_tree.links.new(blend_node.inputs['Color1'], tex_image_node.outputs['Color'])
        material.node_tree.links.new(bsdf.inputs['Emission'], blend_node.outputs['Color'])
        
        # create the alpha blend node
        blend_node = material.node_tree.nodes.new('ShaderNodeMath')
        blend_node.inputs[0].default_value = 1.0
        blend_node.operation = 'MULTIPLY'
        blend_node.label = "Alpha"
        blend_node.location = mathutils.Vector((-260.0, -200.0))
        
        material.node_tree.links.new(blend_node.inputs[1], tex_image_node.outputs['Alpha'])
        material.node_tree.links.new(bsdf.inputs['Alpha'], blend_node.outputs[0])
        
        
        return {'FINISHED'}
        
# -------------------------------------------------------------------	
#   Drawing	
# -------------------------------------------------------------------   

class ANGEL_PT_MaterialHelperPanel(bpy.types.Panel):
    bl_label = "Angel Tools: Quick Setup"	
    bl_idname = "OBJECT_PT_material_helper_panel"	
    bl_space_type = "PROPERTIES"   	
    bl_region_type = "WINDOW"	
    bl_context = "material"	
    bl_category = "Angel Tools" 

    @classmethod	
    def poll(self,context):
        ob = context.active_object
        mat = ob.active_material
        return mat is not None
        
    def draw(self, context):
        layout = self.layout
        layout.operator("angel.create_material_setup")
        
# -------------------------------------------------------------------	
#   Register & Unregister	
# -------------------------------------------------------------------

classes = (	
    CreateMaterialSetupOperator,
    ANGEL_PT_MaterialHelperPanel
)	

def register():        	
    from bpy.utils import register_class	
    for cls in classes:	
        register_class(cls)	


def unregister():	
    from bpy.utils import unregister_class	
    for cls in reversed(classes):	
        unregister_class(cls)	

