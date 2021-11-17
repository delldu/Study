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
from . import op
from . import ui
# from . import nc

bl_info = {
    "name": "AI Video",
    "description": "AI Power for Blender VSE",
    "author": "Dell Du",
    "version": (1, 0),
    "blender": (2, 93, 0),
    "wiki_url": "",
    "tracker_url": "",
    "category": "Sequencer",
}


def register():
    print("Hello, AI Video !")
    op.register()
    ui.register()


def unregister():
    op.unregister()
    ui.unregister()
    print("Goodbye, AI Video !")


if __name__ == "__main__":
    register()
