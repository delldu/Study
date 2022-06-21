import bpy
import time

from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import PointerProperty, StringProperty, FloatProperty


class VideoSMaskSettings(PropertyGroup):
    url: StringProperty(
        name="URL",
        description="Server address",
        default="localhost:9999",
    )

    threshold: FloatProperty(
        name="Treshold",
        description="The min likeness with template",
        default=0.50,
        min=0.0,
        max=1.0,
    )


# VIDEO_OT_SMask
# VIDEO_OT_Color
# VIDEO_OT_Clean
# VIDEO_OT_Zoomx
# VIDEO_OT_Slowx


class VIDEO_OT_SMask(Operator):
    bl_idname = "video.smask"
    bl_label = "SMask"
    bl_description = "Search Mask with AI"

    def execute(self, context):
        settings = context.scene.video_smask_settings
        print(settings.url)

        print("bl_idname = ", self.bl_idname)
        print("bl_label = ", self.bl_label)
        print("bl_description = ", self.bl_description)

        return {"FINISHED"}


class VIDEO_PT_SMask(Panel):
    bl_label = "SMask"
    bl_category = "SMask"
    # bl_space_type = "CLIP_EDITOR"
    bl_space_type = "SEQUENCE_EDITOR"

    bl_region_type = "UI"

    @classmethod
    def poll(cls, context):
        try:
            sc = context.space_data
            print("sc.mode, view = ", sc.mode, sc.view)
            return True
            # return sc.mode == "MASK" and sc.view == "CLIP"
        except:
            pass
        return True

    def draw(self, context):
        layout = self.layout
        settings = context.scene.video_smask_settings
        layout.prop(settings, "url")
        layout.prop(settings, "threshold")
        layout.operator("video.smask", icon="MOD_MASK")


classes = (VIDEO_OT_SMask, VIDEO_PT_SMask, VideoSMaskSettings)


def register():
    from bpy.utils import register_class

    for cls in classes:
        register_class(cls)
    bpy.types.Scene.video_smask_settings = PointerProperty(type=VideoSMaskSettings)


def unregister():
    from bpy.utils import unregister_class

    for cls in reversed(classes):
        unregister_class(cls)
    del bpy.types.Scene.video_smask_settings


if __name__ == "__main__":
    register()


