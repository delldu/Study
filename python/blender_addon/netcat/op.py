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
