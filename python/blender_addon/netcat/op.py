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
from bpy.types import Operator
from bpy.utils import register_classes_factory

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


# import bpy
# from os.path import join

# S = bpy.context.scene
# n = S.node_tree

# vidNode = n.nodes['Movie Clip']

# # Set Render Settings dimensions according to video
# S.render.resolution_percentage = 100
# S.render.resolution_y          = vidNode.clip.size[1]
# S.render.resolution_x          = vidNode.clip.size[0]

# # Render desired frame numbers ( UPDATE THESE AS NEEDED )
# start = 5
# end   = 200
# step  = 3
# frame_numbers = range(start, end, step)

# outputFolder = "C:/tmp/test"    # <=== Update this 
# for f in frame_numbers:
#     S.frame_set( f )
#     fileName = str(f) + S.render.file_extension
#     S.render.filepath = join( outputFolder, fileName )
#     bpy.ops.render.render( write_still = True )


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



class NetcatStartOperator(Operator):
    """Start netcat server"""

    bl_idname = "netcat.start"
    bl_label = "Start Netcat Server"
    bl_options = {"REGISTER"}

    def execute(self, context):

        return {"FINISHED"}


class NetcatStopOperator(Operator):
    """Start netcat server"""

    bl_idname = "netcat.stop"
    bl_label = "Stop Netcat Server"
    bl_options = {"REGISTER"}

    def execute(self, context):

        return {"FINISHED"}


classes = (
    NetcatStartOperator,
    NetcatStopOperator,
)

netcat_register, netcat_unregister = register_classes_factory(classes)


def register():
    netcat_register()


def unregister():
    netcat_unregister()
