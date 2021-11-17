"""AI Power"""
# coding=utf-8
#
# /************************************************************************************
# ***
# ***    Copyright Dell 2020, All Rights Reserved.
# ***
# ***    File Author: Dell, 2021年 11月 12日 星期五 03:00:26 CST
# ***
# ************************************************************************************/
#

import bpy
from bpy.types import (
    Menu,
    # Panel,
)
from bpy.utils import (
    register_class,
    unregister_class,
)

from . import op


class AIVideoMenu(Menu):
    bl_label = "AI"
    bl_idname = "POWER_SEQUENCER_MT_ai_video"

    def draw(self, context):
        layout = self.layout

        layout.operator_context = "INVOKE_DEFAULT"

        layout.operator(op.AI_Video_OT_Scene.bl_idname, icon="SCENE")
        layout.separator()
        layout.operator(op.AI_Video_OT_Clean.bl_idname, icon="BRUSH_DATA")
        layout.operator(op.AI_Video_OT_Color.bl_idname, icon="COLORSET_02_VEC")
        layout.operator(op.AI_Video_OT_Light.bl_idname, icon="OUTLINER_OB_LIGHT")
        layout.operator(op.AI_Video_OT_Smooth.bl_idname, icon="CON_CAMERASOLVER")
        layout.separator()
        layout.operator(op.AI_Video_OT_SMask.bl_idname, icon="MOD_MASK")
        layout.operator(op.AI_Video_OT_PMask.bl_idname, icon="SHADING_BBOX")
        layout.operator(op.AI_Video_OT_Patch.bl_idname, icon="PARTICLE_PATH")
        layout.separator()
        layout.operator(op.AI_Video_OT_Zoom.bl_idname, icon="ZOOM_IN")
        layout.operator(op.AI_Video_OT_Slow.bl_idname)
        layout.separator()
        layout.operator(op.AI_Video_OT_Face.bl_idname, icon="SURFACE_NTORUS")
        layout.operator(op.AI_Video_OT_Pose.bl_idname, icon="POSE_HLT")


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
