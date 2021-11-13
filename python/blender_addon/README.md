## 1. Install
```pip install pynng
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
https://github.com/tin2tin/shot_detection
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

pip install pynng

# Install pynng to blender 2.93 ?
pip install pynng --target=/home/dell/.config/blender/2.93/scripts/addons/modules/
sys.path.append("/home/dell/.config/blender/2.93/scripts/addons/modules/")
import pynng

ls -lh /tmp/xxxx/pynng
total 2.6M
-rw-r--r-- 1 dell dell 7.7K 10月 19 16:28 _aio.py
-rw-r--r-- 1 dell dell 4.0K 10月 19 16:28 exceptions.py
-rw-r--r-- 1 dell dell  933 10月 19 16:28 __init__.py
-rwxr-xr-x 1 dell dell 2.5M 10月 19 16:28 _nng.abi3.so
-rw-r--r-- 1 dell dell  56K 10月 19 16:28 nng.py
-rw-r--r-- 1 dell dell 6.8K 10月 19 16:28 options.py
drwxr-xr-x 2 dell dell 4.0K 10月 19 16:28 __pycache__
-rw-r--r-- 1 dell dell 3.7K 10月 19 16:28 sockaddr.py
-rw-r--r-- 1 dell dell 5.2K 10月 19 16:28 tls.py
-rw-r--r-- 1 dell dell   89 10月 19 16:28 _version.py

pkgutil
list(pkgutil.iter_modules())


https://github.com/tin2tin/shot_detection
https://github.com/amb/blender_pip/blob/master/__init__.py

```
## 2. Server
```
import socket
import sys
import bpy

HOST = '127.0.0.1'
PORT = 65432

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))

# listen() marks the socket referred to by sockfd as a passive socket (awaits for an in­coming connection,
# which will spawn a new active socket once a connection is established), that is, as a socket that
# will be used to accept incoming connection requests using accept(2).
s.listen()

# Extracts the first connection request on the queue of pending connections for the listening socket,
# sockfd, creates a new connected socket, and returns a new file descriptor referring to that socket.
# The newly created socket is not in the listening state. The original socket sockfd is unaffected by
# this call.
conn, addr = s.accept()
conn.settimeout(2.0)

def handle_data():
    interval = 2.0
    #print('Connected by: ', addr)
    data = None

    # In non-blocking mode blocking operations error out with OS specific errors.
    # https://docs.python.org/3/library/socket.html#notes-on-socket-timeouts
    try:
        data = conn.recv(1024)
    except:
        pass

    if not data:
        pass
    else:
        conn.sendall(data)
       
        # Fetch the 'Sockets' collection or create one. Anything created via sockets will be linked
        # to that collection.
        collection = None
        try:
            collection = bpy.data.collections["Sockets"]
        except:
            collection = bpy.data.collections.new("Sockets")
            bpy.context.scene.collection.children.link(collection)

        if "cube" in data.decode("utf-8"):
            mesh_data = bpy.data.meshes.new(name='m_cube')
            obj = bpy.data.objects.new('cube', mesh_data)
            collection.objects.link(obj)

        if "empty" in data.decode("utf-8"):
            empty = bpy.data.objects.new("empty", None)
            empty.empty_display_size = 2
            empty.empty_display_type = 'PLAIN_AXES'
            collection.objects.link(empty)


        if "quit" in data.decode("utf-8"):
            conn.close()
            s.close()

    return interval

bpy.app.timers.register(handle_data)
```
## 3. Client
```
https://github.com/Botmasher/blender-vse-customizations/blob/master/vse/maskomatic.py
https://github.com/lukas-blecher/AutoMask
https://github.com/kbsezginel/blenditioner/blob/master/blenditioner.py
https://github.com/yushulx/snap-package
https://blender.stackexchange.com/questions/221110/fastest-way-copying-from-bgl-buffer-to-numpy-array


Application Handlers (bpy.app.handlers)
https://docs.blender.org/api/current/bpy.app.handlers.html#basic-handler-example

Including 3rd party modules in a Blender addon
https://blender.stackexchange.com/questions/8509/including-3rd-party-modules-in-a-blender-addon

xenogenesi/blender_movieclip_dlib_landmarks.py
https://gist.github.com/xenogenesi/fc4ec4ecebec4861db87ff633dea6347

https://docs.blender.org/api/current/bpy.app.timers.html
https://www.programcreek.com/python/example/127720/bpy.app

bpy.ops.wm.read_factory_settings()
https://github.com/lunadigital/blender-addon-template/blob/master/ui.py
https://gitee.com/kaiv2/blender-addons-contrib/blob/master/space_clip_editor_autotracker.py
https://www.cnblogs.com/yaoyu126/p/9310857.html


bpy.context.scene['mydataparams'] = {'value':1}

dns = bpy.app.driver_namespace
dns["netcat_send_queue"] = queue.Queue()
dns["netcat_recv_queue"] = queue.Queue()
print(dns.get("netcat_send_queue"))
 
```

## 4. Reference Patchs
### General
```
user_preferences = bpy.context.preferences.addons['blenderkit'].preferences
api_key = user_preferences.api_key

def selection_get():
    aob = bpy.context.view_layer.objects.active
    selobs = bpy.context.view_layer.objects.selected[:]
    return (aob, selobs)

# cube=bpy.context.view_layer.objects.active
# type(bpy.context.view_layer.objects.selected) -- <class 'bpy_prop_collection'>
# bpy.context.view_layer.objects.selected[:] -- [bpy.data.objects['Cube']]

def get_active_model():
    if bpy.context.view_layer.objects.active is not None:
        ob = bpy.context.view_layer.objects.active
        while ob.parent is not None:
            ob = ob.parent
        return ob
    return None

img = bpy.data.images.load(path)
bpy.data.images.get('abc.png')
bpy.data.objects.get('Cube')

def img_to_preview(img, copy_original = False):
    if bpy.app.version[0]>=3:
        img.preview_ensure()
    if not copy_original:
        return;
    if img.preview.image_size != img.size:
        img.preview.image_size = (img.size[0], img.size[1])
        img.preview.image_pixels_float = img.pixels[:]

for o in bpy.data.objects: print(o)
# <bpy_struct, Object("Camera") at 0x7f2f369b1208>
# <bpy_struct, Object("Cube") at 0x7f2f402e5808>

for i in bpy.data.images: print(i)
# <bpy_struct, Image("Render Result") at 0x7f2f369b1808>
# <bpy_struct, Image("Viewer Node") at 0x7f2f1800d808>
# len(bpy.data.images) -- 2

def get_addon_thumbnail_path(name):
    script_path = os.path.dirname(os.path.realpath(__file__))
    # fpath = os.path.join(p, subpath)
    ext = name.split('.')[-1]
    next = ''
    if not (ext == 'jpg' or ext == 'png'):  # already has ext?
        next = '.jpg'
    subpath = "thumbnails" + os.sep + name + next
    return os.path.join(script_path, subpath)

def get_hierarchy(ob):
    '''get all objects in a tree'''
    obs = []
    doobs = [ob]
    # pprint('get hierarchy')
    pprint(ob.name)
    while len(doobs) > 0:
        o = doobs.pop()
        doobs.extend(o.children)
        obs.append(o)
    return obs
 
 def get_scene_id():
    '''gets scene id and possibly also generates a new one'''
    bpy.context.scene['uuid'] = bpy.context.scene.get('uuid', str(uuid.uuid4()))
    return bpy.context.scene['uuid']
 
 def get_app_version():
    ver = bpy.app.version
    return '%i.%i.%i' % (ver[0], ver[1], ver[2])


def register_download():
    bpy.utils.register_class(BlenderkitDownloadOperator)
    bpy.utils.register_class(BlenderkitKillDownloadOperator)
    bpy.app.handlers.load_post.append(scene_load)
    bpy.app.handlers.save_pre.append(scene_save)
    user_preferences = bpy.context.preferences.addons['blenderkit'].preferences
    if user_preferences.use_timers:
        bpy.app.timers.register(download_timer)
        
def create_blank_image(image_name, dimensions, alpha=1):
    """Create a new image and assign white color to all its pixels"""
    image_name = image_name[:64]
    width, height = int(dimensions.x), int(dimensions.y)
    image = bpy.data.images.new(image_name, width, height, alpha=True)
    if image.users > 0:
        raise UnfoldError(
            "There is something wrong with the material of the model. "
            "Please report this on the BlenderArtists forum. Export failed.")
    image.pixels = [1, 1, 1, alpha] * (width * height)
    image.file_format = 'PNG'
    return image

# image = bpy.data.images.new("image.png", 1024, 768, True)   
# image.filepath='/tmp/image.png'
# image.save()
# image.reload()

# bpy.context.scene.cycles.bake_type -- 'COMBINED'

# buffer = numpy.empty(1024 * 768 * 4, dtype=numpy.float32)
# image.pixels.foreach_get(buffer)
## set_colorspace(new_image, 'Linear')
# new_image.colorspace_settings.name = 'Linear'
# new_image.pixels.foreach_set(buffer)

def imagetonumpy(i):
    t = time.time()
    import numpy as np
    width = i.size[0]
    height = i.size[1]
    # print(i.channels)
    size = width * height * i.channels
    na = np.empty(size, np.float32)
    i.pixels.foreach_get(na)
    # dropping this re-shaping code -  just doing flat array for speed and simplicity
    # na = na[::4]
    na = na.reshape(height, width, i.channels)
    na = na.swapaxes(0, 1)
    # print('\ntime of image to numpy ' + str(time.time() - t))
    return na


def imagetonumpy_flat(i):
    t = time.time()
    import numpy
    width = i.size[0]
    height = i.size[1]
    # print(i.channels)
    size = width * height * i.channels
    na = numpy.empty(size, numpy.float32)
    i.pixels.foreach_get(na)
    # print('\ntime of image to numpy ' + str(time.time() - t))
    return na

def get_rgb_mean(i):
    import numpy
    na = imagetonumpy_flat(i)
    # start:stop:step, [r1, g1, b1, a1], [r2,g2,b2, a2, ...]
    r = na[0::4]
    g = na[1::4]
    b = na[2::4]
    rmean = r.mean()
    gmean = g.mean()
    bmean = b.mean()
    return (rmean, gmean, bmean)
    
image.preview.image_size = (image.size[0], image.size[1])
image.preview.image_pixels_float[:] = image.pixels

bpy.utils.register_classes_factory

list_mem = list_members = lambda x: [e for e in dir(x) if not e.startswith("_")]
list_members(bpy.context)
[e for e in list_members(image) if 'file' in e.lower()]

list_for = list_forall = lambda x: [e for e in x]
# bpy.data.movieclips.keys()
movie = bpy.data.movieclips.get('tennis.mp4')
# bpy.data.masks.keys() -- ['Mask', 'Mask.001']


grease = bpy.data.grease_pencils[0]
# -- bpy.data.grease_pencils['Annotations']

strip = bpy.context.scene.sequence_editor.active_strip
strip.type -- "MOVIE"

list_for(bpy.context.scene.sequence_editor.sequences)
# [bpy.data.scenes['Scene'].sequence_editor.sequences_all["tennis.mp4"], 
#  bpy.data.scenes['Scene'].sequence_editor.sequences_all["001.png"]
v = bpy.context.scene.sequence_editor.sequences[0]
p = bpy.context.scene.sequence_editor.sequences[1]
# v.type -- 'MOVIE'
# p.type -- 'IMAGE'

bpy.context.scene.node_tree.nodes

mask = bpy.data.masks['Mask']
spline = mask.layers['MaskLayer'].splines[0]
for p in spline.points:
    p.handle_left_type = 'FREE'
    p.handle_right_type = 'FREE'
    p.co[0] -= 0.1
    p.co[1] -= 0.1

```

### MCE
```
list_for(bpy.data.movieclips) -- [bpy.data.movieclips['tennis.mp4']]
clip = bpy.data.movieclips[0]
clip.filepath -- '/home/dell/tennis.mp4'
clip.source -- 'MOVIE'
clip.frame_start, clip.frame_duration, clip.frame_offset -- (1, 70, 0)

bpy.context.scene -- bpy.data.scenes['Scene']
bpy.data.scenes['Scene'].frame_current -- 40
bpy.context.scene.frame_start, bpy.context.scene.frame_end -- (1, 70)
bpy.context.scene.frame_current -- 41

mask = bpy.data.masks[0]
list_for(mask.layers) -- [bpy.data.masks['Mask'].layers["MaskLayer"]]

layer = mask.layers[0]
layer = mask.layers.active -- bpy.data.masks['Mask'].layers["MaskLayer"]
list_mem(layer) -- ['alpha', 'bl_rna', 'blend', 'falloff', 'hide', 'hide_render', 'hide_select', 'invert', 'name', 'rna_type', 'select', 'splines', 'use_fill_holes', 'use_fill_overlap']

def hide_layer(layer, hide=True):
    layer.hide = hide
    layer.hide_render = hide
    layer.hide_select = hide
    layer.keyframe_insert('hide')
    layer.keyframe_insert('hide_render')
    layer.keyframe_insert('hide_select')
    
    
import bpy
frameStart = 1
frameEnd = 155
frameStep = 50
viewer_area = None
viewer_space = None

for area_search in bpy.context.screen.areas:
    if viewer_area == None and area_search.type == "IMAGE_EDITOR":
        viewer_area = area_search
        break

if viewer_area == None:
    viewer_area = bpy.context.screen.areas[0]
    viewer_area.type = "IMAGE_EDITOR"

for space in viewer_area.spaces:
    if space.type == "IMAGE_EDITOR":
        viewer_space = space

path = "/home/dell/noise.mp4"
img = bpy.data.images.load(path)
w = img.size[0]
h = img.size[1]
viewer_space.image = img

frame = 1
for frame in range(1, 50, 10):
    viewer_space.image_user.frame_offset = frame
    #switch back and forth to force refresh
    viewer_space.draw_channels = 'COLOR_ALPHA'
    viewer_space.draw_channels = 'COLOR'
    pixels = list(viewer_space.image.pixels)
    tmp = bpy.data.images.new(name="sample"+str(frame), width=w, height=h, alpha=False, float_buffer=False)
    tmp.pixels = pixels

img.user_clear()
bpy.data.images.remove(img)

```

```
img = bpy.data.images.load("/home/dell/noise.mp4")
img.pixels -- bpy.data.images['noise.mp4'].pixels
dir(img.pixels) -- ['foreach_get', 'foreach_set']

import numpy as np
w, h = img.size
n = img.frame_duration
pixel_data = np.zeros((w, h, 4), 'f')
img.pixels.foreach_get(pixel_data.ravel())
print(pixel_data.mean(), pixel_data.std())
```





### VSE

```
def doc_idname(s): return ".".join(map(str.lower, s.split("_OT_")))
doc_idname('POWER_SEQUENCER_OT_space_sequences') -- 'power_sequencer.space_sequences'

bpy.context.scene.sequence_editor_create()
bpy.context.area.type = 'SEQUENCE_EDITOR'

s=bpy.context.scene.sequence_editor.sequences.new_movie("tennis.mp4", "/home/dell/tennis.mp4", channel=1, frame_start=1, fit_method='ORIGINAL')

s=bpy.context.scene.sequence_editor.sequences.new_movie("color.mp4", "", channel=3, frame_start=1)
s.frame_final_duration = 70
s.blend_alpha = 0.5

bpy.context.scene.sequence_editor.sequences.new_image(...)
bpy.context.scene.sequence_editor.sequences.new_effect()

import bpy
def get_sequencer_area():
    sequencer_area = None
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if not area.type == "SEQUENCE_EDITOR":
                continue
            sequencer_area = {
            "window": window,
            "screen": window.screen,
            "area": area,
            "scene": bpy.context.scene,
            }
    return sequencer_area

bpy.context.scene.sequence_editor_create()
bpy.context.area.type = 'SEQUENCE_EDITOR'
bpy.ops.sequencer.movie_strip_add(
    get_sequencer_area(),
    filepath="/home/dell/tennis.mp4",
    frame_start=1,
    sound=1,
    use_framerate=1)

bpy.context.window_manager.progress_begin(0, 100)
bpy.context.window_manager.progress_update(50)
bpy.context.window_manager.progress_end()

bpy.context.selected_sequences
bpy.context.scene.sequence_editor.sequences.new_effect(name="bug", type="TEXT", channel=1, frame_start=1, frame_end=70)




import bpy
from pathlib import Path

dir_path = "/home/dell/ZDisk/Workspace/develop/VideoXYZ/clean/dataset/predict/input/"
img_dir = Path(dir_path)
glob = "*.png"
frame_duration = 24
files = sorted(list(img_dir.glob(glob)))

# get sequence editor
scene = bpy.context.scene
#scene.sequence_editor_clear()
sed = scene.sequence_editor_create()
seq = sed.sequences
duration = len(files)
# add image strip using first
fp = files.pop(0)
imstrip = seq.new_image(
    name="newvideo.mp4",
    filepath=str(fp),
    frame_start=1,
    channel=1,
    )
# add the elements 
while files:
    imstrip.elements.append(files.pop(0).name)
    
imstrip.frame_final_duration = duration
imstrip.update() 

https://blender.stackexchange.com/questions/46601/how-to-load-a-movie-file-into-blender-and-re-export-it-as-a-sequence-of-images
```

### Render

```
bpy.context.scene.render -- bpy.data.scenes['Scene'].render
bpy.data.scenes['Scene'].render.resolution_x
bpy.data.scenes['Scene'].render.resolution_percentage -- 100


import bpy
def my_handler(scene):
    print("Frame Change", scene.frame_current)
    bpy.data.scenes['Scene'].sequence_editor.sequences_all["Text"].text=str(int(scene.frame_current/10))
bpy.app.handlers.frame_change_pre.append(my_handler)

Animate a Character in 15 Minutes in Blender
https://github.com/DeepBlender/DeepDenoiser/tree/master/Blender
https://www.immersivelimit.com/tutorials/blender-for-ai-developers

https://github.com/Cartucho/vision_blender

```

```
# AUTHOR Luigi
# VERSION 0.0.1
#功能：直接渲染特定帧viewport画面
#分为三步，首先关闭 viewport overlays,第二步跳转到指定的帧，第三部渲染并自动命名。二三步为循环。最后再打开overlay。

import bpy
import time

for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        for space in area.spaces:
            if space.type == 'VIEW_3D':
                space.overlay.show_overlays=False #turn off viewport layout
                break

list = ['55', '90', '125'] #set the list of frame you want
OUTPUT = "C:/Users/luigi/Pictures"   # Where to save Images

for i in list:
    bpy.context.scene.frame_set(int(i)) #jump to frame
    timenow = time.strftime("%m%d %H%M%S", time.localtime()) #add timemark
    filepath = OUTPUT + "/" + str(timenow) + ".png"
    bpy.context.scene.render.filepath = filepath
    bpy.ops.render.opengl(write_still=True, view_context=True) #render viewport
```


### Annotation

```
bpy.data.grease_pencils[0] -- bpy.data.grease_pencils['Annotations']
bpy.data.grease_pencils[1] -- bpy.data.grease_pencils['Annotations.001']
pen = bpy.data.grease_pencils[0]
pen.layers[0].frames -- bpy.data.grease_pencils['Annotations'].layers["Note"].frames
s = pen.layers[0].frames[0].strokes
for p in s.data.strokes[0].points:
	print(p.co.x, p.co.y, p.co.z)
	
f =  bpy.data.grease_pencils['Annotations'].layers['Note'].frames[0]
dir(f) -- ['frame_number','strokes']
bpy.data.movieclips['noise.mp4'].grease_pencil
# -- bpy.data.grease_pencils['cbox']



```

### Tracker

```
https://gitlab.com/ChameleonScales/step_tracker/
https://blender.stackexchange.com/questions/41150/parent-for-trackers-with-python-script
https://blenderartists.org/t/tracker-data/572292/3
```



### Keyframe

```
bpy.app.debug_wm = True

def refresh_ui_keyframes():
    try:
        for area in bpy.context.screen.areas:
            if area.type in ('TIMELINE', 'GRAPH_EDITOR', 'DOPESHEET_EDITOR'):
                area.tag_redraw()
    except:
        pass

track = bpy.data.movieclips['tennis.mp4'].tracking.tracks["Track.001"]
markers = bpy.data.movieclips['tennis.mp4'].tracking.tracks["Track.001"].markers
```

```
import bpy
from mathutils import (
    Vector,
)

def MarkerSize():
    clip = bpy.data.movieclips['tennis.mp4']
    track = clip.tracking.tracks[0]
    marker = track.markers[0]
    pattern = Vector(marker.pattern_bound_box[1]) - Vector(marker.pattern_bound_box[0])

    clip_width = clip.size[0]
    clip_height = clip.size[1]

	height = int(pattern[1] * clip_height)
    width = int(pattern[0] * clip_width)

	row = height - int(marker.co[1] * clip_height)
    col = int(marker.co[0] * clip_width)

	print("file path:", clip.filepath)
	print("current frame:", bpy.context.scene.frame_current)
    print(f"Marker: center_row = {row}, center_col = {col}, half_height = {height}, half_width = {width}")
   
MarkerSize()

```

```
import bpy

def MaskSize():
    clip = bpy.data.movieclips['tennis.mp4']
    
    clip_width = clip.size[0]
    clip_height = clip.size[1]

    visiable_points = []
    for mask in bpy.data.masks:
        if not mask.use_fake_user:
            continue
        for layer in mask.layers:
            for s in layer.splines:
                for p in s.points:
                    visiable_points.append(p)

    print("------------------")
    for p in visiable_points:    
        print("x = ", p.co[0], "y = ", p.co[1])

    print("===================")
    min_x = min_y = 1.0
    max_x = max_y = -1.0
    for p in visiable_points:
        min_x = min(min_x, p.co[0])
        max_x = max(max_x, p.co[0])
        min_y = min(min_y, 1.0 - p.co[1])
        max_y = max(max_y, 1.0 - p.co[1])

    min_x = int(min_x * clip_width)
    max_x = int(max_x * clip_width)
    min_y = int(min_y * clip_height)
    max_y = int(max_y * clip_height)
    
    print("file path:", clip.filepath)
    print("clip: h x w = ", clip_height, "x", clip_width)
    
    print("current frame:", bpy.context.scene.frame_current)
    print(f"Mask: min_x = {min_x}, min_y = {min_y}, max_x = {max_x}, max_y = {max_y}")
   
MaskSize()
```

```
import bpy
import threading,time

class Create_obj:
    def __init__(self,name):
        self.obj = bpy.data.objects[name]
    
    def obj_loc(self,data):
        self.obj.location[2] = data

    def obj_animation(self,data,fra):
        self.obj.location[2] = data
        self.obj.keyframe_insert(data_path="location",frame=fra,index=2)


if __name__ == "__main__":
    obj_1 = Create_obj('Cube')
    data = iter(([i*0.1 for i in range(30)]+[3-i*0.1 for i in range(30)])*100)
    def test(ed):
        global obj_1,data
        st = time.time()
        while time.time()-st<ed:
            print("working")
            obj_1.obj_loc(next(data))
            time.sleep(0.05)
            
        print("done")
        # 打印的信息可以在blender的系统控制台查看

    def animation(ed):
        global obj_1,data

        st = time.time()
        fra = 0#blender默认一秒24帧
        while time.time()-st<ed:
            print(fra)
            
            obj_1.obj_animation(next(data),fra)
            
            time.sleep(0.05)
            fra += 1
        print("done")

    t=threading.Thread(target=animation,args=(10,))
    t.start()
```

Panel

```
tex = bpy.data.textures.new(name='Texture', type='IMAGE')


# tex = bpy.data.textures['.hidden']
col = layout.box().column()
col.template_preview(tex)

```



### Socket

```
_presets = os.path.join(bpy.utils.user_resource('SCRIPTS'), "presets")
BLENDERKIT_LOCAL = "http://localhost:8001"
BLENDERKIT_MAIN = "https://www.blenderkit.com"
BLENDERKIT_DEVEL = "https://devel.blenderkit.com"
BLENDERKIT_API = "/api/v1/"
BLENDERKIT_REPORT_URL = "usage_report/"
BLENDERKIT_USER_ASSETS = "/my-assets"
BLENDERKIT_PLANS = "/plans/pricing/"
BLENDERKIT_MANUAL = "https://youtu.be/pSay3yaBWV0"
BLENDERKIT_MODEL_UPLOAD_INSTRUCTIONS_URL = "https://www.blenderkit.com/docs/upload/"
BLENDERKIT_MATERIAL_UPLOAD_INSTRUCTIONS_URL = "https://www.blenderkit.com/docs/uploading-material/"
BLENDERKIT_BRUSH_UPLOAD_INSTRUCTIONS_URL = "https://www.blenderkit.com/docs/uploading-brush/"
BLENDERKIT_HDR_UPLOAD_INSTRUCTIONS_URL = "https://www.blenderkit.com/docs/uploading-hdr/"
BLENDERKIT_SCENE_UPLOAD_INSTRUCTIONS_URL = "https://www.blenderkit.com/docs/uploading-scene/"
BLENDERKIT_LOGIN_URL = "https://www.blenderkit.com/accounts/login"
BLENDERKIT_OAUTH_LANDING_URL = "/oauth-landing/"
BLENDERKIT_SIGNUP_URL = "https://www.blenderkit.com/accounts/register"
BLENDERKIT_SETTINGS_FILENAME = os.path.join(_presets, "bkit.json")

```

## 5. Development

   ```
list_foreach = lambda x: [e for e in x]

list_members = lambda x: [f"{e}: {getattr(x, e)}" for e in dir(x) if not e.startswith("_") and  getattr(x,e ) is not None]

def print_members(x, pattern=None):
    import re
    elements = [e for e in dir(x) if not e.startswith("_") and getattr(x,e) is not None]
    for e in elements:
        if pattern is None:
            print(e, ":", getattr(x,e))
        elif re.match(pattern, e):
            print(e, ":", getattr(x,e))

   ```

## 6. Learning

   ```
   https://www.zcool.com.cn/article/ZMTI3MTc4OA==.html
   https://github.com/cgvirus/Blender-Compositor-Extra-Nodes
   bpy.data.node_groups[0].nodes['Custom Node']['my_string_prop']
   
   CustomNodeGroupTemplate
   https://pastebin.com/gnF0iS7B
   
   animation nodes和sverchock
   https://github.com/cgvirus/Blender-Compositor-Disc-Cache-Realtime-Preview-Addon
   
   https://github.com/cgvirus/blender-vse-easy-proxy
   
   https://blender.stackexchange.com/questions/71454/is-it-possible-to-make-a-sequence-of-renders-and-give-the-user-the-option-to-can
   
https://ostechnix.com/20-ffmpeg-commands-beginners/
   ```

### Panel

```
import bpy
from bpy.types import Panel


import bpy
def every_2_seconds():
    print("Hello World")
    return 2.0
bpy.app.timers.register(every_2_seconds)
https://docs.blender.org/api/current/bpy.app.timers.html
https://github.com/snuq/VSEQF


https://blender.stackexchange.com/questions/95722/how-to-detect-scene-strips-in-the-vse-on-frame-changes

https://zwolf12.medium.com/video-scene-detection-and-classification-pyscenedetect-places365-and-mozilla-deepspeech-engine-51338e3dbacc

```

