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
import os
import bpy
from bpy.types import Operator
from bpy.utils import register_classes_factory

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


AI_VIDEO_CACHE_PATH = "/tmp/ai_video"


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


def active_image():
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
    grease pencils is global share under VSE
    current implement only supoort one box
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
                # box = [frame_number, x1, x2, y1, y2]
                return [f.frame_number, min(xset), max(xset), min(yset), max(yset)]
    except:
        pass
    return None


def aviable_channel():
    channel = 0
    seqs = current_sequences()
    for s in seqs:
        channel = max(s.channel, channel)
    return channel + 1


class VideoStrips(object):
    """Todo List: data[s.name] = id"""

    def __init__(self):
        self.data = {}

    def put(self, name, id):
        self.data[name] = id
        print("video Todo List:", self.data)

    def get(self, name):
        return self.data.get(name, None)

    def delete(self, name):
        try:
            del self.data[name]
        except:
            pass

    def size(self):
        return len(self.data)

    def names(self):
        return [e for e in self.data.keys()]


video_todo_list = VideoStrips()


def ai_video_timer():
    timer_duration = 2.0
    global video_todo_list

    print(f"ai video timer {timer_duration}")
    if video_todo_list.size() < 1:
        return timer_duration

    seqs = current_sequences()
    if len(seqs) < 1:
        return timer_duration

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
            id = video_todo_list.get(s.name)
            if id:
                print("video task id: ", id)
                task_done_percent = 0.50
                s.blend_alpha = -0.2 * task_done_percent + 0.8

    return timer_duration


class AIVideoOperator(Operator):
    """General Class for Video Operator"""

    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        strip = active_strip()
        return strip and strip.type == "MOVIE"

    def create_strip(self, name):
        try:
            a = active_strip()
            # a.frame_start, a.frame_duration
            seqs = current_sequences()
            name = name + "_" + os.path.basename(a.filepath)
            s = seqs.get(name, None)
            if s is None:
                # new_movie(name, filepath, channel, frame_start)
                s = seqs.new_movie(
                    name,
                    f"{AI_VIDEO_CACHE_PATH}/{name}",
                    channel=aviable_channel(),
                    frame_start=a.frame_start,
                )
                s.frame_start = a.frame_start
                s.frame_final_duration = a.frame_duration
                s.blend_alpha = 1.0
                new_movie = True
            else:
                new_movie = False
        except:
            return None, None, False

        return s, a, new_movie


class AI_Video_OT_Scene(AIVideoOperator):
    """Auto cut scenes"""

    bl_idname = "ai_video.scene"
    bl_label = "Scene"

    def execute(self, context):
        # scene = context.scene
        # cursor = scene.cursor.location
        # obj = context.active_object

        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)


class AI_Video_OT_Clean(AIVideoOperator):
    """Video clean"""

    bl_idname = "ai_video.clean"
    bl_label = "Clean"

    sigma: IntProperty(
        name="Sigma",
        description="The noise level",
        default=25,
        min=0,
        max=100,
    )

    def execute(self, context):
        # scene = context.scene
        # cursor = scene.cursor.location
        # obj = context.active_object
        s, a, new_movie = self.create_strip("clean")
        if new_movie and s and a:
            cmd = f"clean(infile={a.filepath},sigma=30,outfile={s.filepath})"
            video_todo_list.put(s.name, "xxxx_id")

        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=480)


class AI_Video_OT_Color(AIVideoOperator):
    """Video color"""

    bl_idname = "ai_video.color"
    bl_label = "Color"

    def execute(self, context):
        reference_image = active_image()
        if reference_image is None:
            self.report({"WARNING"}, "NO image for reference." "Operation Cancelled")
            return {"CANCELLED"}

        self.create_strip("color")
        return {"FINISHED"}


class AI_Video_OT_Light(AIVideoOperator):
    """Light enhance"""

    bl_idname = "ai_video.light"
    bl_label = "Light"

    def execute(self, context):
        self.create_strip("light")

        return {"FINISHED"}


class AI_Video_OT_Smooth(AIVideoOperator):
    """Video smooth"""

    bl_idname = "ai_video.smooth"
    bl_label = "Smooth"

    def execute(self, context):
        self.create_strip("smooth")
        return {"FINISHED"}


class AI_Video_OT_SMask(AIVideoOperator):
    """Siamese Mask"""

    bl_idname = "ai_video.smask"
    bl_label = "SMask"

    def execute(self, context):
        box = active_bbox()
        if box is None:
            self.report(
                {"WARNING"},
                "NO annotation or less points (< 4) for boundling box."
                "Operation Cancelled",
            )
            return {"CANCELLED"}
        print("bbox == ", bbox)
        self.create_strip("smask")

        return {"FINISHED"}


class AI_Video_OT_PMask(AIVideoOperator):
    """Panoptic Mask"""

    bl_idname = "ai_video.pmask"
    bl_label = "PMask"

    def execute(self, context):
        self.create_strip("pmask")

        return {"FINISHED"}


class AI_Video_OT_Patch(AIVideoOperator):
    """Video patch"""

    bl_idname = "ai_video.patch"
    bl_label = "Patch"

    def execute(self, context):
        self.create_strip("patch")
        return {"FINISHED"}


class AI_Video_OT_Zoom(AIVideoOperator):
    """Zoom in 4x"""

    bl_idname = "ai_video.zoom"
    bl_label = "Zoom"

    def execute(self, context):
        self.create_strip("zoom")
        return {"FINISHED"}


class AI_Video_OT_Slow(AIVideoOperator):
    """Slow down"""

    bl_idname = "ai_video.slow"
    bl_label = "Slow"

    slow: IntProperty(
        name="Slow down", description="The slow down times", default=2, min=2, max=4
    )

    def execute(self, context):
        self.create_strip("slow")

        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class AI_Video_OT_Face(AIVideoOperator):
    """Driving face"""

    bl_idname = "ai_video.face"
    bl_label = "Face"

    def execute(self, context):
        face_image = active_image()
        if face_image is None:
            self.report({"WARNING"}, "NO face image." "Operation Cancelled")
            return {"CANCELLED"}

        self.create_strip("face")

        return {"FINISHED"}


class AI_Video_OT_Pose(AIVideoOperator):
    """Driving pose"""

    bl_idname = "ai_video.pose"
    bl_label = "Pose"

    def execute(self, context):
        face_image = active_image()
        if face_image is None:
            self.report({"WARNING"}, "NO pose image." "Operation Cancelled")
            return {"CANCELLED"}

        self.create_strip("pose")
        return {"FINISHED"}


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
    except:
        print(f"Create directory '{path}' error.")


def register():
    ai_video_register()

    create_dir(AI_VIDEO_CACHE_PATH)
    bpy.app.timers.register(ai_video_timer)


def unregister():
    ai_video_unregister()
    bpy.app.timers.unregister(ai_video_timer)
