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
        description="Choose the game path, used to fallback to default textures etc. (Game data must be unpacked)"
    )

    use_gamepath: bpy.props.BoolProperty(
        name="Use Game Path", 
        default = True
    )
    
    substitute_textures: bpy.props.BoolProperty(
        name="Substitute Textures", 
        description = "Replace missing textures with a pink and black checkerboard pattern. This will keep texture assignments intact in case a texture is missing.",
        default = True
    )
    
    use_alpha_hash: bpy.props.BoolProperty(
        name="Prefer Alpha Hash For Blend Mode", 
        description = "Use alpha hash instead alpha blend on transparent materials. May make transparency appear incorrectly, but solves objects rendering atop each other.",
        default = False
    )
  
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "substitute_textures")
        layout.prop(self, "use_alpha_hash")
        layout.prop(self, "use_gamepath")
        layout.prop(self, "gamepath")



classes = (PkgPreferences,)

register_factory, unregister_factory = bpy.utils.register_classes_factory(classes)


def register():
    register_factory()


def unregister():
    unregister_factory()
