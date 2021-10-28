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
