## 1. Install
```pip install pynng
https://blender.stackexchange.com/questions/8509/including-3rd-party-modules-in-a-blender-addon


https://github.com/yushulx/snap-package


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


https://github.com/yushulx/snap-package


xenogenesi/blender_movieclip_dlib_landmarks.py
https://blender.stackexchange.com/questions/221110/fastest-way-copying-from-bgl-buffer-to-numpy-array
https://stackoverflow.com/questions/58790877/blender-api-rendering-a-frame-to-memory


####
https://docs.blender.org/api/current/bpy.app.handlers.html#basic-handler-example

###
https://blender.stackexchange.com/questions/80195/how-to-get-the-truly-width-and-height-of-frame-when-rendering-it-would-be-good
```
## 2. Server
```

```
## 3. Client
```

```

## 4. Reference Patchs
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

```

