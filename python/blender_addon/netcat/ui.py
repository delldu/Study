"""Blender Addon Netcat"""
# coding=utf-8
#
# /************************************************************************************
# ***
# ***    Copyright Dell 2020, All Rights Reserved.
# ***
# ***    File Author: Dell, 2020年 09月 09日 星期三 23:56:45 CST
# ***
# ************************************************************************************/
#

import bpy
from bpy.types import (
    Panel,
)
from bpy.utils import (
    register_class,
    unregister_class,
)

from bpy.props import (
    IntProperty,
)


class NetcatPanel(Panel):
    """Creates a Panel for netcat broker"""

    bl_label = "Netcat Broker"
    bl_idname = "SCENE_PT_netcat"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_options = {"DEFAULT_CLOSED"}

    listen_port: IntProperty(
        name="Listen Port",
        description="A integer for netcat listen port",
        default=9999,
        min=1024,
        max=65535,
    )

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.label(text="Netcat Broker", icon="WORLD_DATA")

        row = layout.row()
        row.prop(self, "list_port", slider=True)

        row = layout.row()
        row.label(text="Wait Sending Messages: 256")
        row = layout.row()
        row.label(text="Received Messages: 1024")


def register():
    register_class(NetcatPanel)


def unregister():
    unregister_class(NetcatPanel)


if __name__ == "__main__":
    register()
