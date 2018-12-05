# import os
import numpy as np


def start_connect_visdom():
    try:
        import visdom
        vis = visdom.Visdom(raise_exceptions=True)
    except:
        print("Could not connect to visdom server, please make sure:")
        print("1. install visdom:")
        print("   pip insall visdom")
        print("2. start visdom server: ")
        print("   python -m visdom.server &")
        return None
    else:
        return vis

vis = start_connect_visdom()
if (vis is not None):
    vis.text("Hello, world !")
    vis.image(np.ones((3, 10, 10)))
