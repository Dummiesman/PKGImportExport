import bpy
import re
from bpy.types import (Panel,
                       Menu,
                       Operator,
                       PropertyGroup,
                       UIList
                       )
                       
from bpy.props import (IntProperty,
                       FloatProperty,
                       BoolProperty,
                       StringProperty,
                       CollectionProperty,
                       FloatVectorProperty,
                       EnumProperty,
                       PointerProperty)

# -------------------------------------------------------------------
#   Properties
# -------------------------------------------------------------------
class ANGEL_SuspensionProperties(PropertyGroup):
    scale:  FloatVectorProperty(name='Axis Aligned Scale',subtype='XYZ',size=3,default=(0.0,0.0,0.0))
    alignment:  FloatVectorProperty(name='Alignment',subtype='XYZ',size=3,default=(0.0,0.0,0.0))
      
# -------------------------------------------------------------------
#   Drawing
# -------------------------------------------------------------------      
class OBJECT_PT_SuspensionPanel(Panel):
    bl_label = "Angel Tools: Suspension Setup"
    bl_idname = "OBJECT_PT_suspension_panel"
    bl_space_type = "PROPERTIES"   
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_category = "Angel Tools" 

    @staticmethod
    def is_suspension_object(obj):
        obj_name = obj.name.lower()
        return (obj_name == "axle0_h" or obj_name == "axle1_h" or obj_name == "shock0_h" or obj_name == "shock1_h" or obj_name == "shock2_h" or obj_name == "shock3_h" 
                or obj_name == "arm0_h" or obj_name == "arm1_h" or obj_name == "arm2_h" or obj_name == "arm3_h" or obj_name == "shaft2_h" or obj_name == "shaft3_h")

    @classmethod
    def poll(self,context):
        active_obj = context.active_object
        if active_obj is None:
            return False
        return OBJECT_PT_SuspensionPanel.is_suspension_object(active_obj)

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        obj = context.active_object
        
        suspension_settings = obj.suspension_settings
       
        layout.prop(suspension_settings, "scale")
        layout.prop(suspension_settings, "alignment")
        


# -------------------------------------------------------------------
#   Register & Unregister
# -------------------------------------------------------------------

classes = (
    OBJECT_PT_SuspensionPanel,
    ANGEL_SuspensionProperties
)

def register():        
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    bpy.types.Object.suspension_settings = bpy.props.PointerProperty(type=ANGEL_SuspensionProperties)

    
def unregister():
    from bpy.utils import unregister_class
    del bpy.types.Object.suspension_settings
    for cls in reversed(classes):
        unregister_class(cls)


    
    