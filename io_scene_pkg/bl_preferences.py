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
