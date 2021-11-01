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
    "name": "AI Video",
    "description": "AI Power for Blender VSE",
    "author": "Dell Du",
    "version": (1, 0),
    "blender": (2, 93, 0),
    "wiki_url": "",
    "tracker_url":"",
    "category": "Sequencer"}

from . import op
from . import ui

def register():
    print("Hello, AI Video !")
    op.register()
    ui.register()

def unregister():
    op.unregister()
    ui.unregister()
    print("Goodbye, AI Video !")

if __name__ == '__main__':
    register()

