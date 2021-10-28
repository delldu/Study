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

bl_info = {
    "name": "Netcat",
    "description": "A Network Broker for Blender",
    "author": "Dell Du",
    "version": (1, 0),
    "blender": (2, 93, 0),
    "wiki_url": "",
    "tracker_url": "",
    "category": "System",
}

from . import op
from . import ui


def register():
    print("Hello, Netcat !")
    op.register()
    ui.register()


def unregister():
    op.unregister()
    ui.unregister()
    print("Goodbye, Netcat !")


if __name__ == "__main__":
    register()
