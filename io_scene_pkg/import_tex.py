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

def register():
    bpy.utils.register_class(ImportTEX)


def unregister():
    bpy.utils.unregister_class(ImportTEX)