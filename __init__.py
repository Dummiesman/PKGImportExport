# ##### BEGIN LICENSE BLOCK #####
#
# This program is licensed under Creative Commons Attribution-NonCommercial-ShareAlike 3.0
# https://creativecommons.org/licenses/by-nc-sa/3.0/
#
# Copyright (C) Dummiesman, 2016
#
# ##### END LICENSE BLOCK #####

bl_info = {
    "name": "Midtown Madness 2 PKG Format",
    "author": "Dummiesman",
    "version": (0, 1, 2),
    "blender": (2, 76, 0),
    "location": "File > Import-Export",
    "description": "Import-Export PKG files",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
                "Scripts/Import-Export/PKG",
    "support": 'COMMUNITY',
    "category": "Import-Export"}

import bpy
from bpy.props import (
        BoolProperty,
        EnumProperty,
        FloatProperty,
        StringProperty,
        CollectionProperty,
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
    filter_glob = StringProperty(default="*.pkg", options={'HIDDEN'})

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
    filter_glob = StringProperty(
            default="*.pkg",
            options={'HIDDEN'},
            )

    additional_paintjobs = StringProperty(
        name="Material Replacement Info",
        description="This is used for extra paintjobs. This list is structured like : _yellow_,_green|_yellow_,_red_  etc.",
        default="",
        )
    
    g_autobound = BoolProperty(
        name="Auto Bound",
        description="Generate a MM2 style bound for vehicle exports",
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
    self.layout.operator(ExportPKG.bl_idname, text="Midtown Madness 2 (.pkg)")


def menu_func_import(self, context):
    self.layout.operator(ImportPKG.bl_idname, text="Midtown Madness 2 (.pkg)")


def register():
    bpy.utils.register_module(__name__)

    bpy.types.INFO_MT_file_import.append(menu_func_import)
    bpy.types.INFO_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_module(__name__)

    bpy.types.INFO_MT_file_import.remove(menu_func_import)
    bpy.types.INFO_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":
    register()