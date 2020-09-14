# ##### BEGIN LICENSE BLOCK #####
#
# This program is licensed under Creative Commons BY-NC-SA:
# https://creativecommons.org/licenses/by-nc-sa/3.0/
#
# Created by Dummiesman, 2016-2020
#
# ##### END LICENSE BLOCK #####

bl_info = {
    "name": "Angel Studios PKG Format",
    "author": "Dummiesman",
    "version": (1, 0, 0),
    "blender": (2, 83, 0),
    "location": "File > Import-Export",
    "description": "Import-Export PKG files",
    "warning": "",
    "doc_url": "https://github.com/Dummiesman/PKGImportExport/",
    "tracker_url": "https://github.com/Dummiesman/PKGImportExport/",
    "support": 'COMMUNITY',
    "category": "Import-Export"}

import bpy
import io_scene_pkg.variant_ui as variant_ui
import io_scene_pkg.angel_scenedata as angel_scenedata
import io_scene_pkg.bl_preferences as bl_preferences

from bpy.props import (
        BoolProperty,
        EnumProperty,
        FloatProperty,
        StringProperty,
        CollectionProperty,
        IntProperty,
        PointerProperty
        )
from bpy_extras.io_utils import (
        ImportHelper,
        ExportHelper,
        )

class ImportPKG(bpy.types.Operator, ImportHelper):
    """Import from PKG file format (.pkg)"""
    bl_idname = "import_scene.pkg"
    bl_label = 'Import PKG'
    bl_options = {'UNDO'}

    filename_ext = ".pkg"
    filter_glob: StringProperty(default="*.pkg", options={'HIDDEN'})

    def execute(self, context):
        from . import import_pkg
        keywords = self.as_keywords(ignore=("axis_forward",
                                            "axis_up",
                                            "filter_glob",
                                            "check_existing",
                                            ))

        return import_pkg.load(self, context, **keywords)


class ExportPKG(bpy.types.Operator, ExportHelper):
    """Export to PKG file format (.PKG)"""
    bl_idname = "export_scene.pkg"
    bl_label = 'Export PKG'

    filename_ext = ".pkg"
    filter_glob: StringProperty(
            default="*.pkg",
            options={'HIDDEN'},
            )

    e_vertexcolors: BoolProperty(
        name="Vertex Colors (Diffuse)",
        description="Export vertex colors that affect diffuse",
        default=False,
        )
        
    e_vertexcolors_s: BoolProperty(
        name="Vertex Colors (Specular)",
        description="Export vertex colors that affect specular",
        default=False,
        )
        
    apply_modifiers: BoolProperty(
        name="Apply Modifiers",
        description="Do you desire modifiers to be applied in the PKG?",
        default=True,
        )
        
    selection_only: BoolProperty(
        name="Selection Only",
        description="Export only selected elements",
        default=False,
        )
        
    def execute(self, context):
        from . import export_pkg
        
        keywords = self.as_keywords(ignore=("axis_forward",
                                            "axis_up",
                                            "filter_glob",
                                            "check_existing",
                                            ))
                                    
        return export_pkg.save(self, context, **keywords)


# Add to a menu
def menu_func_export(self, context):
    self.layout.operator(ExportPKG.bl_idname, text="Angel Studios ModPackage (.pkg)")


def menu_func_import(self, context):
    self.layout.operator(ImportPKG.bl_idname, text="Angel Studios ModPackage (.pkg)")

# Register factories
classes = (
    ImportPKG,
    ExportPKG
)

def register():
    bl_preferences.register()
    for cls in classes:
        bpy.utils.register_class(cls)
    angel_scenedata.register()
    variant_ui.register()
    
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    
    bpy.types.Material.variant = bpy.props.IntProperty(name="Variant")
    bpy.types.Material.cloned_from = bpy.props.PointerProperty(name="Cloned From", type=bpy.types.Material)
    
    bpy.types.Scene.angel = PointerProperty(type=angel_scenedata.AngelSceneData)


def unregister():
    del bpy.types.Scene.angel
    del bpy.types.Material.cloned_from
    del bpy.types.Material.variant 
    
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

    variant_ui.unregister()
    angel_scenedata.unregister()
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    bl_preferences.unregister()
    

if __name__ == "__main__":
    register()
