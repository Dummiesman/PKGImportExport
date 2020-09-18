 # ##### BEGIN LICENSE BLOCK #####
#
# This program is licensed under Creative Commons BY-NC-SA:
# https://creativecommons.org/licenses/by-nc-sa/3.0/
#
# Created by Dummiesman, 2016-2020
#
# ##### END LICENSE BLOCK #####

import bpy

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

class ImportTEX(bpy.types.Operator, ImportHelper):
    """Import image from Angel Studios TEX file format"""
    bl_idname = "import_texture.tex"
    bl_label = 'Import TEX Image'
    bl_options = {'UNDO'}

    filename_ext = ".tex"
    filter_glob: StringProperty(default="*.tex", options={'HIDDEN'})

    def execute(self, context):
        from io_scene_pkg.tex_file import TEXFile
        keywords = self.as_keywords(ignore=("axis_forward",
                                            "axis_up",
                                            "filter_glob",
                                            "check_existing",
                                            ))
        filepath = self.properties.filepath
        imagename = bpy.path.display_name_from_filepath(self.properties.filepath)
        
        tex = TEXFile(filepath)
        tex.to_blender_image(imagename)
        
        return {'FINISHED'}

class ImportTEXMenu(bpy.types.Menu):
    bl_idname = "ANGEL_MT_import_tex_menu"
    bl_label = "Angel Tools"

    def draw(self, context):
        layout = self.layout

        layout.operator("import_texture.tex")
        
    def menu_draw(self, context):
        self.layout.menu("ANGEL_MT_import_tex_menu")


def register():
    bpy.utils.register_class(ImportTEXMenu)
    bpy.utils.register_class(ImportTEX)
    bpy.types.TOPBAR_MT_editor_menus.append(ImportTEXMenu.menu_draw)


def unregister():
    bpy.types.TOPBAR_MT_editor_menus.remove(ImportTEXMenu.menu_draw)
    bpy.utils.unregister_class(ImportTEX)
    bpy.utils.unregister_class(ImportTEXMenu)