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
import os
import bpy
from bpy.types import Operator
from bpy.utils import register_classes_factory

from bpy.props import (
    # BoolProperty,
    IntProperty,
    # StringProperty,
)
from . import app
from . import nc

# Global variables
AI_VIDEO_CACHE_PATH = "/tmp/ai_video"
video_todo_list = app.VideoStrips()
ai_video_timer_duration = 2.0
ai_video_nc = nc.NCClient("localhost", 9999)


def ai_video_timer():
    if video_todo_list.size() < 1:
        return ai_video_timer_duration

    print(f"ai video timer {ai_video_timer_duration}")
    seqs = current_sequences()
    if len(seqs) < 1:
        return ai_video_timer_duration

    names = video_todo_list.names()
    for s in seqs:
        if s.name not in names:
            continue

        # s.name is created ai video operator
        if os.path.exists(s.filepath):
            s.blend_alpha = 1.0
            # task done, we delete it from video strips
            video_todo_list.delete(s.name)
        else:
            # update progress
            id = video_todo_list.get(s.name)
            if id:
                percent = ai_video_nc.get(id) / 100.0
                s.blend_alpha = -0.2 * percent + 0.8

    return ai_video_timer_duration


def current_sequences():
    try:
        return bpy.context.scene.sequence_editor.sequences
    except AttributeError:
        return []


def image_sequences():
    seqs = current_sequences()
    return [s for s in seqs if s.type == "IMAGE"]


def movie_sequences():
    seqs = current_sequences()
    return [s for s in seqs if s.type == "MOVIE"]


def active_strip():
    try:
        return bpy.context.scene.sequence_editor.active_strip
        # context.area.spaces.active.clip
    except AttributeError:
        return None


def active_bimage():
    """Find bundling image"""

    images = image_sequences()
    if len(images) < 1:
        return None

    a = active_strip()
    if a is None:
        return images[0]

    # closest image with active strip
    smin = images[0]
    dmin = abs(smin.channel - a.channel)
    for i in range(1, len(images)):
        d = abs(images[i].channel - a.channel)
        if d < dmin:
            dmin = d
            smin = images[i]
    return smin


def active_bbox():
    """
    Bundling box
    1) Grease pencils is global under VSE
    2) Current implement only supoort one box
    """
    try:
        h = bpy.data.scenes["Scene"].render.resolution_y
        w = bpy.data.scenes["Scene"].render.resolution_x
        for f in bpy.data.grease_pencils[0].layers[0].frames:
            # print("frame_number: ", f.frame_number)
            # one time draw --> one box
            for s in f.strokes:
                if len(s.points) < 4:
                    continue
                xset = [0.5 + p.co.x / w for p in s.points]
                yset = [0.5 - p.co.y / h for p in s.points]
                # box big enough ?
                if max(xset) - min(xset) < 0.01 or max(yset) - min(yset) < 0.01:
                    continue
                # box = [frame_number, x1, x2, y1, y2]
                return {
                    "nframe": f.frame_number,
                    "x1": min(xset),
                    "x2": max(xset),
                    "y1": min(yset),
                    "y2": max(yset),
                }
    except Exception:
        pass
    return None


def aviable_channel():
    channel = 0
    seqs = current_sequences()
    for s in seqs:
        channel = max(s.channel, channel)
    return channel + 1


def create_bstrip(a, prefix):
    """
    Create bundling strip, a means activte_strip
    """
    try:
        seqs = current_sequences()
        if len(seqs) < 1:
            return None

        name = prefix + "_" + os.path.basename(a.filepath)
        s = seqs.get(name, None)
        if s is None:
            # protype: new_movie(name, filepath, channel, frame_start)
            s = seqs.new_movie(
                name,
                f"{AI_VIDEO_CACHE_PATH}/{name}",
                channel=aviable_channel(),
                frame_start=a.frame_start,
            )
            s.frame_start = a.frame_start
            s.frame_final_duration = a.frame_duration
            s.blend_alpha = 1.0
            return s
    except Exception:
        pass
    return None


class AIVideoOperator(Operator):
    """General Class for Video Operator"""

    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        a = active_strip()
        return a and a.type == "MOVIE"

    def warning(self, message):
        self.report({"WARNING"}, message)

    def setup_task(self, name, cmd):
        ai_video_nc.put(cmd)
        video_todo_list.put(name, nc.nc_id(cmd))


class AI_Video_OT_Scene(AIVideoOperator):
    """Auto cut scenes"""

    bl_idname = "ai_video.scene"
    bl_label = "Scene"

    def execute(self, context):
        a = active_strip()
        # a is valid for poll method

        s = create_bstrip(a, "scene")
        if s is None:
            self.warning("Scene task is going on ... ?")
            return {"CANCELLED"}

        cmd = app.VideoCommand.scene(a.filepath, s.filepath)
        self.setup_task(s.name, cmd)

        return {"FINISHED"}


class AI_Video_OT_Clean(AIVideoOperator):
    """Video clean"""

    bl_idname = "ai_video.clean"
    bl_label = "Clean"

    sigma: IntProperty(
        name='sigma',
        description='The noise level',
        default=25,
        min=0,
        max=100,
    )

    def execute(self, context):
        a = active_strip()
        # a is valid for poll method

        s = create_bstrip(a, "clean")
        if s is None:
            self.warning("Clean task is going on ... ?")
            return {"CANCELLED"}

        cmd = app.VideoCommand.clean(a.filepath, self.sigma, s.filepath)
        self.setup_task(s.name, cmd)

        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=256)


class AI_Video_OT_Color(AIVideoOperator):
    """Video color"""

    bl_idname = "ai_video.color"
    bl_label = "Color"

    def execute(self, context):
        color_image = active_bimage()
        if color_image is None:
            self.warning("NO color image for reference")
            return {"CANCELLED"}

        a = active_strip()
        # a is valid for poll method
        s = create_bstrip(a, "color")
        if s is None:
            self.warning("Color task is going on ... ?")
            return {"CANCELLED"}

        cmd = app.VideoCommand.color(a.filepath, color_image.filepath, s.filepath)
        self.setup_task(s.name, cmd)

        return {"FINISHED"}


class AI_Video_OT_Light(AIVideoOperator):
    """Light enhance"""

    bl_idname = "ai_video.light"
    bl_label = "Light"

    def execute(self, context):
        a = active_strip()
        # a is valid for poll method
        s = create_bstrip(a, "light")
        if s is None:
            self.warning("Light task is going on ... ?")
            return {"CANCELLED"}

        cmd = app.VideoCommand.light(a.filepath, s.filepath)
        self.setup_task(s.name, cmd)

        return {"FINISHED"}


class AI_Video_OT_Smooth(AIVideoOperator):
    """Video smooth"""

    bl_idname = "ai_video.smooth"
    bl_label = "Smooth"

    def execute(self, context):
        a = active_strip()
        # a is valid for poll method

        s = create_bstrip(a, "smooth")
        if s is None:
            self.warning("Smooth task is going on ... ?")
            return {"CANCELLED"}

        cmd = app.VideoCommand.smooth(a.filepath, s.filepath)
        self.setup_task(s.name, cmd)

        return {"FINISHED"}


class AI_Video_OT_SMask(AIVideoOperator):
    """Siamese Mask"""

    bl_idname = "ai_video.smask"
    bl_label = "SMask"

    def execute(self, context):
        bbox = active_bbox()
        if bbox is None:
            self.warning("NO annotation or less points (< 4) for bbox")
            return {"CANCELLED"}
        # print("bbox == ", bbox)

        a = active_strip()
        # a is valid for poll method
        s = create_bstrip(a, "smask")
        if s is None:
            self.warning("SMask task is going on ... ?")
            return {"CANCELLED"}

        cmd = app.VideoCommand.smask(
            a.filepath,
            bbox["nframe"],
            bbox["x1"],
            bbox["x2"],
            bbox["y1"],
            bbox["y2"],
            s.filepath,
        )
        self.setup_task(s.name, cmd)

        return {"FINISHED"}


class AI_Video_OT_PMask(AIVideoOperator):
    """Panoptic Mask"""

    bl_idname = "ai_video.pmask"
    bl_label = "PMask"

    def execute(self, context):
        a = active_strip()
        # a is valid for poll method
        s = create_bstrip(a, "pmask")
        if s is None:
            self.warning("PMask task is going on ... ?")
            return {"CANCELLED"}

        cmd = app.VideoCommand.pmask(a.filepath, s.filepath)
        self.setup_task(s.name, cmd)

        return {"FINISHED"}


class AI_Video_OT_Patch(AIVideoOperator):
    """Video patch"""

    bl_idname = "ai_video.patch"
    bl_label = "Patch"

    def execute(self, context):
        a = active_strip()
        # a is valid for poll method
        s = create_bstrip(a, "patch")
        if s is None:
            self.warning("Patch task is going on ... ?")
            return {"CANCELLED"}

        cmd = app.VideoCommand.patch(a.filepath, s.filepath)
        self.setup_task(s.name, cmd)


class AI_Video_OT_Zoom(AIVideoOperator):
    """Zoom in 4x"""

    bl_idname = "ai_video.zoom"
    bl_label = "Zoom"

    def execute(self, context):
        a = active_strip()
        # a is valid for poll method
        s = create_bstrip(a, "zoom")
        if s is None:
            self.warning("Zoom task is going on ... ?")
            return {"CANCELLED"}

        cmd = app.VideoCommand.zoom(a.filepath, s.filepath)
        self.setup_task(s.name, cmd)


class AI_Video_OT_Slow(AIVideoOperator):
    """Slow down"""

    bl_idname = "ai_video.slow"
    bl_label = "Slow"

    slow: IntProperty(
        name="slow", description='The slow down times', default=2, min=2, max=4
    )

    def execute(self, context):
        a = active_strip()
        # a is valid for poll method
        s = create_bstrip(a, "slow")
        if s is None:
            self.warning("Slow task is going on ... ?")
            return {"CANCELLED"}

        cmd = app.VideoCommand.slow(a.filepath, self.slow, s.filepath)
        self.setup_task(s.name, cmd)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class AI_Video_OT_Face(AIVideoOperator):
    """Driving face"""

    bl_idname = "ai_video.face"
    bl_label = "Face"

    def execute(self, context):
        face_image = active_bimage()
        if face_image is None:
            self.warning("NO target face image")
            return {"CANCELLED"}

        a = active_strip()
        # a is valid for poll method
        s = create_bstrip(a, "face")
        if s is None:
            self.warning("Face task is going on ... ?")
            return {"CANCELLED"}

        cmd = app.VideoCommand.face(a.filepath, face_image.filepath, s.filepath)
        self.setup_task(s.name, cmd)

        return {"FINISHED"}


class AI_Video_OT_Pose(AIVideoOperator):
    """Driving pose"""

    bl_idname = "ai_video.pose"
    bl_label = "Pose"

    def execute(self, context):
        pose_image = active_bimage()
        if pose_image is None:
            self.warning("NO target pose image")
            return {"CANCELLED"}

        a = active_strip()
        # a is valid for poll method
        s = create_bstrip(a, "pose")
        if s is None:
            self.warning("Pose task is going on ... ?")
            return {"CANCELLED"}

        cmd = app.VideoCommand.pose(a.filepath, pose_image.filepath, s.filepath)
        self.setup_task(s.name, cmd)


classes = (
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

ai_video_register, ai_video_unregister = register_classes_factory(classes)


def create_dir(path):
    try:
        if os.path.exists(path) and not os.path.isdir(path):
            os.removedirs(path)
        if not os.path.exists(path):
            os.makedirs(path)
    except Exception as e:
        print(f"Create directory '{path}' error:", e)


def register():
    ai_video_register()

    create_dir(AI_VIDEO_CACHE_PATH)
    bpy.app.timers.register(ai_video_timer)


def unregister():
    ai_video_unregister()
    bpy.app.timers.unregister(ai_video_timer)

    ai_video_nc.close()
