import onnx
import numpy as np
import tvm
from tvm import te
import tvm.relay as relay
from tvm.contrib.download import download_testdata

import pdb

model_path = 'super_resolution.onnx'
onnx_model = onnx.load(model_path)
# '/home/dell/.tvm_test_data/onnx/super_resolution.onnx'

from PIL import Image
img_path = 'cat.png'
img = Image.open(img_path).resize((224, 224))
img_ycbcr = img.convert("YCbCr")  # convert to YCbCr
img_y, img_cb, img_cr = img_ycbcr.split()
x = np.array(img_y)[np.newaxis, np.newaxis, :, :]


target = "llvm"
input_name = "1"
shape_dict = {input_name: x.shape}
mod, params = relay.frontend.from_onnx(onnx_model, shape_dict)

with tvm.transform.PassContext(opt_level=1):
    intrp = relay.build_module.create_executor("graph", mod, tvm.cpu(0), target)


######################################################################
# Execute on TVM
# ---------------------------------------------
input = tvm.nd.array(x.astype("float32"))
tvm_output = intrp.evaluate()(input, **params).asnumpy()


# pdb.set_trace()
# tvm_output.shape -- (1, 1, 672, 672)

from matplotlib import pyplot as plt

out_y = Image.fromarray(np.uint8((tvm_output[0, 0]).clip(0, 255)), mode="L")
out_cb = img_cb.resize(out_y.size, Image.BICUBIC)
out_cr = img_cr.resize(out_y.size, Image.BICUBIC)
result = Image.merge("YCbCr", [out_y, out_cb, out_cr]).convert("RGB")
canvas = np.full((672, 672 * 2, 3), 255)
canvas[0:224, 0:224, :] = np.asarray(img)
canvas[:, 672:, :] = np.asarray(result)
plt.imshow(canvas.astype(np.uint8))
plt.show()

######################################################################
# Notes
# ---------------------------------------------
# By default, ONNX defines models in terms of dynamic shapes. The ONNX importer
# retains that dynamism upon import, and the compiler attemps to convert the model
# into a static shapes at compile time. If this fails, there may still be dynamic
# operations in the model. Not all TVM kernels currently support dynamic shapes,
# please file an issue on discuss.tvm.apache.org if you hit an error with dynamic kernels.
#
# This particular model was build using an older version of ONNX. During the import
# phase ONNX importer will run the ONNX verifier, which may throw a `Mismatched attribute type`
# warning. Because TVM supports a number of different ONNX versions, the Relay model
# will still be valid.


print("------------------------------------")

target = tvm.target.Target("llvm", host="llvm")
dev = tvm.cpu(0)
with tvm.transform.PassContext(opt_level=3):
    lib = relay.build(mod, target=target, params=params)


from torchvision import transforms

my_preprocess = transforms.Compose(
    [
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ]
)

img = Image.open(img_path).resize((224, 224)).convert("RGB")


img = my_preprocess(img)
img = np.expand_dims(img, 0)


from tvm.contrib import graph_executor

dtype = "float32"
m = graph_executor.GraphModule(lib["default"](dev))
# Set inputs
m.set_input(input_name, tvm.nd.array(img.astype(dtype)))
# Execute
m.run()
# Get outputs
tvm_output = m.get_output(0)