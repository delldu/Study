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

from op import (
    AI_Video_OT_Scene,
    AI_Video_OT_Clean,
    AI_Video_OT_Color,
    AI_Video_OT_Light,
    AI_Video_OT_Smooth,
    AI_Video_OT_SMask,
    AI_Video_OT_PMask,
    AI_Video_OT_Patch,
    AI_Video_OT_Zoom,
    AI_Video_OT_Slow,
    AI_Video_OT_Face,
    AI_Video_OT_Pose,
)

class AIVideoMenu(Menu):
    bl_label = "AI"
    bl_idname = "POWER_SEQUENCER_MT_ai_video"

    def draw(self, context):
        layout = self.layout

        layout.operator_context = 'INVOKE_DEFAULT'

        layout.operator(AI_Video_OT_Scene.bl_idname, icon='SCENE')
        layout.separator()
        layout.operator(AI_Video_OT_Clean.bl_idname, icon='BRUSH_DATA')
        layout.operator(AI_Video_OT_Color.bl_idname, icon='COLORSET_02_VEC')
        layout.operator(AI_Video_OT_Light.bl_idname, icon='OUTLINER_OB_LIGHT')
        layout.operator(AI_Video_OT_Smooth.bl_idname, icon='CON_CAMERASOLVER')
        layout.separator()
        layout.operator(AI_Video_OT_SMask.bl_idname, icon='MOD_MASK')
        layout.operator(AI_Video_OT_PMask.bl_idname, icon='SHADING_BBOX')
        layout.operator(AI_Video_OT_Patch.bl_idname, icon='PARTICLE_PATH')
        layout.separator()
        layout.operator(AI_Video_OT_Zoom.bl_idname, icon='ZOOM_IN')
        layout.operator(AI_Video_OT_Slow.bl_idname)
        layout.separator()
        layout.operator(AI_Video_OT_Face.bl_idname, icon='SURFACE_NTORUS')
        layout.operator(AI_Video_OT_Pose.bl_idname, icon='POSE_HLT')


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
