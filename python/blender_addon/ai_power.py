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


bl_info = {
    "name": "AI Power",
    "description": "AI Power tools for video sequencer",
    "author": "Dell Du",
    "version": (1, 0),
    "blender": (2, 93, 0),
    "wiki_url": "",
    "tracker_url":"",
    "category": "Sequencer"}

import bpy
from bpy.types import (
    Menu,
    Panel,
    Operator
)
from bpy.utils import (
    register_class,
    unregister_class,
    register_classes_factory
)

from bpy.props import (
    # BoolProperty,
    IntProperty,
    StringProperty,
)


# bpy.ops.sequencer.fades_add()
# bpy.ops.sequencer.fades_clear()
# bpy.context.scene.sequence_editor.active_strip.frame_final_duration -- 70

# seqs = bpy.context.scene.sequence_editor.sequences
# seqs.keys() -- ['tennis.mp4', 'Transform']

# elem = strip.strip_elem_from_frame(scene.frame_current)

# bpy.data.scenes['Scene'].frame_current -- 35
# bpy.data.scenes['Scene'].frame_set(20)
# C.scene.frame_set(C.scene.frame_current + 1)

# [i.frame for i in bpy.context.scene.timeline_markers]

def act_strip(context):
    try:
        return bpy.context.scene.sequence_editor.active_strip
    except AttributeError:
        return None

class AIVideoOperator(Operator):
    """ Abstract Class for Video Operator"""
    @classmethod
    def poll(cls, context):
        strip = act_strip(context)
        if not strip:
            return False
        return strip.type != 'SOUND'


    def render(self, context):
        scene = context.scene
        render = scene.render

        scene.frame_start = 1
        scene.frame_end = 25

        render.resolution_x = 1280
        render.resolution_y = 720
        render.fps = 25

        render.image_settings.file_format = 'FFMPEG'
        render.ffmpeg.format = 'MPEG4'
        render.ffmpeg.codec = 'H264'

        render.ffmpeg.constant_rate_factor = 'HIGH'
        render.ffmpeg.ffmpeg_preset = 'BEST'

        bpy.ops.render.render(animation=True)



class AIVideoScene(AIVideoOperator):
    """Video Scene"""
    bl_idname = "ai.video_scene"
    bl_label = "Scene"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # scene = context.scene
        # cursor = scene.cursor.location
        # obj = context.active_object
        self.render(context)

        return {'FINISHED'}


class AIVideoClean(AIVideoOperator):
    """Video Clean"""
    bl_idname = "ai.video_clean"
    bl_label = "Clean"
    bl_options = {'REGISTER', 'UNDO'}

    URL: StringProperty(name="URL",
        description="Video Clean Service URL",
        default="http://localhost:9999/clean")

    sigma: IntProperty(
        name="Sigma",
        description="The estimation noise level",
        default=25,
        min=0,
        max=100
    )

    def execute(self, context):
        scene = context.scene
        cursor = scene.cursor.location
        obj = context.active_object

        return {'FINISHED'}

class AIVideoColor(AIVideoOperator):
    """Video Colorization"""
    bl_idname = "ai.video_color"
    bl_label = "Color"
    bl_options = {'REGISTER', 'UNDO'}

    URL: StringProperty(name="URL",
        description="Video Color Service URL",
        default="http://localhost:9999/color")

    def execute(self, context):
        scene = context.scene
        cursor = scene.cursor.location
        obj = context.active_object

        return {'FINISHED'}

class AIVideoLight(AIVideoOperator):
    """Light Enhance"""
    bl_idname = "ai.video_light"
    bl_label = "Light"
    bl_options = {'REGISTER', 'UNDO'}

    URL: StringProperty(name="URL",
        description="Video Light Service URL",
        default="http://localhost:9999/light")

    def execute(self, context):
        scene = context.scene
        cursor = scene.cursor.location
        obj = context.active_object

        return {'FINISHED'}

class AIVideoStable(AIVideoOperator):
    """Video Stabilize"""
    bl_idname = "ai.video_stable"
    bl_label = "Stable"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        cursor = scene.cursor.location
        obj = context.active_object

        return {'FINISHED'}


class AIVideoSMask(AIVideoOperator):
    """Siamese Mask"""
    bl_idname = "ai.video_smask"
    bl_label = "S Mask"
    bl_options = {'REGISTER', 'UNDO'}

    URL: StringProperty(name="URL",
        description="Video Siamese Mask Service URL",
        default="http://localhost:9999/smask")

    # sigma: IntProperty(
    #     name="Sigma",
    #     description="The estimation noise level",
    #     default=25,
    #     min=0
    #     max=100
    # )


    def execute(self, context):
        scene = context.scene
        cursor = scene.cursor.location
        obj = context.active_object

        return {'FINISHED'}


class AIVideoPMask(AIVideoOperator):
    """Panoptic Mask"""
    bl_idname = "ai.video_pmask"
    bl_label = "P Mask"
    bl_options = {'REGISTER', 'UNDO'}

    URL: StringProperty(name="URL",
        description="Video Panoptic Mask Service URL",
        default="http://localhost:9999/pmask")

    def execute(self, context):
        scene = context.scene
        cursor = scene.cursor.location
        obj = context.active_object

        return {'FINISHED'}


class AIVideoPatch(AIVideoOperator):
    """Video Patch"""
    bl_idname = "ai.video_patch"
    bl_label = "Patch"
    bl_options = {'REGISTER', 'UNDO'}

    URL: StringProperty(name="URL",
        description="Video Patch Service URL",
        default="http://localhost:9999/patch")

    def execute(self, context):
        scene = context.scene
        cursor = scene.cursor.location
        obj = context.active_object

        return {'FINISHED'}


class AIVideoZoom(AIVideoOperator):
    """Zoom in"""
    bl_idname = "ai.video_zoom"
    bl_label = "Zoom"
    bl_options = {'REGISTER', 'UNDO'}

    URL: StringProperty(name="URL",
        description="Video Zoom In Service URL",
        default="http://localhost:9999/zoom")

    zoomx: IntProperty(
        name="zoomx",
        description="The scale times",
        default=4,
        min=2,
        max=4
    )

    def execute(self, context):
        scene = context.scene
        cursor = scene.cursor.location
        obj = context.active_object

        return {'FINISHED'}

class AIVideoSlow(AIVideoOperator):
    """Video Slow"""
    bl_idname = "ai.video_slow"
    bl_label = "Slow"
    bl_options = {'REGISTER', 'UNDO'}

    URL: StringProperty(name="URL",
        description="Video Slow Service URL",
        default="http://localhost:9999/slow")

    slowx: IntProperty(
        name="slowx",
        description="The slow down times",
        default=2,
        min=2,
        max=4
    )

    def execute(self, context):
        scene = context.scene
        cursor = scene.cursor.location
        obj = context.active_object

        return {'FINISHED'}

class AIVideoFace(AIVideoOperator):
    """Live face, driving face picture"""
    bl_idname = "ai.video_face"
    bl_label = "Face"
    bl_options = {'REGISTER', 'UNDO'}

    URL: StringProperty(name="URL",
        description="Video Motion Face Service URL",
        default="http://localhost:9999/face")

    def execute(self, context):
        scene = context.scene
        cursor = scene.cursor.location
        obj = context.active_object

        return {'FINISHED'}

class AIVideoPose(AIVideoOperator):
    """Live Pose, driving pose picture"""
    bl_idname = "ai.video_pose"
    bl_label = "Pose"
    bl_options = {'REGISTER', 'UNDO'}

    URL: StringProperty(name="URL",
        description="Video Motion Pose Service URL",
        default="http://localhost:9999/pose")

    def execute(self, context):

        print("Test", self)
        # scene = context.scene
        # cursor = scene.cursor.location
        # obj = context.active_object

        return {'FINISHED'}


class AIVideoMenu(Menu):
    bl_label = "AI"
    bl_idname = "POWER_SEQUENCER_MT_ai.video_menu"

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


classes = (
    AIVideoScene,
    AIVideoClean,
    AIVideoColor,
    AIVideoLight,
    AIVideoStable,
    AIVideoSMask,
    AIVideoPMask,
    AIVideoPatch,
    AIVideoZoom,
    AIVideoSlow,
    AIVideoFace,
    AIVideoPose,
)

ai_video_register, ai_video_unregister = register_classes_factory(classes)


def register():
    print("Hello, AI Power")
    ai_video_register()

    register_class(AIVideoMenu)
    bpy.types.SEQUENCER_HT_header.prepend(draw_item)

def unregister():
    ai_video_unregister()
    unregister_class(AIVideoMenu)
    bpy.types.SEQUENCER_HT_header.remove(draw_item)

    print("Goodbye, AI Power")

            
if __name__ == "__main__":
    register()
