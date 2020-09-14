# ##### BEGIN LICENSE BLOCK #####
#
# This program is licensed under Creative Commons BY-NC-SA:
# https://creativecommons.org/licenses/by-nc-sa/3.0/
#
# Created by Dummiesman, 2016-2020
#
# ##### END LICENSE BLOCK #####

import os
import logging
import random

import bpy

class PkgPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    gamepath: bpy.props.StringProperty(
        name="Game Path",
        description="Choose the game path, used for substituting missing textures etc. (Game data must be unpacked)"
    )

    use_gamepath: bpy.props.BoolProperty(
        name="Use Game Path", 
        default = True
    )

  
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "use_gamepath")
        layout.prop(self, "gamepath")



classes = (PkgPreferences,)

register_factory, unregister_factory = bpy.utils.register_classes_factory(classes)


def register():
    register_factory()


def unregister():
    unregister_factory()
