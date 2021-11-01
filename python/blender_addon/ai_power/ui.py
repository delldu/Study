"""AI Power"""
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
    Menu,
    Panel,
)
from bpy.utils import (
    register_class,
    unregister_class,
)

class AIVideoMenu(Menu):
    bl_label = "AI"
    bl_idname = "POWER_SEQUENCER_MT_ai_video_menu"

    def draw(self, context):
        layout = self.layout
        layout.operator("ai.video_scene")
        layout.separator()
        layout.operator("ai.video_clean")
        layout.operator("ai.video_color")
        layout.operator("ai.video_light")
        layout.operator("ai.video_stable")
        layout.separator()
        layout.operator("ai.video_smask")
        layout.operator("ai.video_pmask")
        layout.operator("ai.video_patch")
        layout.separator()
        layout.operator("ai.video_zoom")
        layout.operator("ai.video_slow")
        layout.separator()
        layout.operator("ai.video_face")
        layout.operator("ai.video_pose")

def draw_item(self, context):
    layout = self.layout
    layout.menu(AIVideoMenu.bl_idname)

def register():
    register_class(AIVideoMenu)
    bpy.types.SEQUENCER_HT_header.prepend(draw_item)
    # bpy.types.CLIP_HT_header

def unregister():
    unregister_class(AIVideoMenu)
    bpy.types.SEQUENCER_HT_header.remove(draw_item)
            
