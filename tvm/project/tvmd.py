"""Onnx Model Tools."""  # coding=utf-8
#
# /************************************************************************************
# ***
# ***    Copyright Dell 2021, All Rights Reserved.
# ***
# ***    File Author: Dell, 2021年 03月 23日 星期二 12:42:57 CST
# ***
# ************************************************************************************/
#

import argparse
import os
import pdb  # For debug
import numpy as np
from PIL import Image

def file_name_ext(filename):
    """return file ext"""
    return os.path.splitext(os.path.basename(filename))[1]

def is_image_file(filename):
    try:
        image = Image.open(filename).convert('RGB')
        return image.height > 0 and image.width > 0
    except:
        # for output case ...
        return file_name_ext(filename).lower() in ['.png', '.jpeg', '.jpg', '.bmp']

def is_numpy_file(filename):
    return file_name_ext(filename) == ".npz"

def image_to_numpy(image_file, numpy_file, normalize=False):
    assert os.path.exists(image_file), f"File {image_file} not exist."

    image = Image.open(image_file)

    numpy_data = np.asarray(image).astype("float32")
    # ONNX expects NCHW input, so convert the array from HxWxC to CxHxW
    numpy_data = np.transpose(numpy_data, (2, 0, 1))

    # Normalize according to ImageNet
    if normalize:
        imagenet_mean = np.array([0.485, 0.456, 0.406])
        imagenet_stdv = np.array([0.229, 0.224, 0.225])
        normal_data = np.zeros(image_data.shape).astype("float32")
        for i in range(numpy_data.shape[0]):
             normal_data[i, :, :] = (numpy_data[i, :, :] / 255 - imagenet_mean[i]) / imagenet_stdv[i]
    else:
        normal_data = np.zeros(numpy_data.shape).astype("float32")
        for i in range(numpy_data.shape[0]):
             normal_data[i, :, :] = numpy_data[i, :, :] / 255

    # Add batch dimension
    numpy_data = np.expand_dims(normal_data, axis=0)
    np.savez(numpy_file, data=numpy_data)

def numpy_to_image(numpy_file, image_file):
    assert os.path.exists(numpy_file), f"File {numpy_file} not exist."
    numpy_data = np.load(numpy_file)

    for k, v in numpy_data.items():
        image_data = numpy_data[k]
        # image_data.shape -- (1, 3, 348, 348)
        image_data = np.squeeze(image_data, axis=0)
        image_data = np.transpose(image_data, (1, 2, 0))    # CxHxW --> HxWxC
        image_data = image_data * 255
        image = Image.fromarray(image_data.astype('uint8'))
        image.save(image_file)
        break   # Save only first one ?

def compare_files(numpy_file1, numpy_file2):
    assert os.path.exists(numpy_file1), f"File {numpy_file1} not exist."
    assert os.path.exists(numpy_file2), f"File {numpy_file2} not exist."
    numpy_data1 = np.load(numpy_file1)
    numpy_data2 = np.load(numpy_file2)
    for k, v in numpy_data1.items():
        image_data1 = numpy_data1[k]
        image_data2 = numpy_data2[k]
        np.testing.assert_allclose(image_data1, image_data2, rtol=1e-03, atol=1e-03)

    for k, v in numpy_data2.items():
        image_data1 = numpy_data1[k]
        image_data2 = numpy_data2[k]
        np.testing.assert_allclose(image_data1, image_data2, rtol=1e-03, atol=1e-03)

    print(f"File {numpy_file1} and {numpy_file2} almost equal.")

if __name__ == "__main__":
    """
    tvmd -- co-worker of tvmc
    """
    parser = argparse.ArgumentParser(
        description="tvmd help tvmc to process image data",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("-i", "--input", type=str, default="", help="input file")
    parser.add_argument("-n", "--normal", help="normal with imagenet mean/std", action="store_true")
    parser.add_argument("-o", "--output", type=str, default="", help="output file")
    parser.add_argument("-c", "--compare", type=str, default="", help="compare file with input")
    args = parser.parse_args()

    def show_help_exit(message):
        print("*" * 80)
        print("*")
        print("* Warning: " + message + ", please kindly reference help")
        print("*")
        print("*" * 80)
        parser.print_help()        
        os._exit(-1)

    if len(args.input) + len(args.output) + len(args.compare) == 0:
        show_help_exit("Missing input, output or compare option")

    if not os.path.exists(args.input):
        show_help_exit(f"File {args.input} not exist.")

    if len(args.output) + len(args.compare) == 0:
        show_help_exit("Missing output or compare option")

    if len(args.output) > 0:
        if is_image_file(args.input) and is_numpy_file(args.output):
            image_to_numpy(args.input, args.output, args.normal)
        elif is_numpy_file(args.input) and is_image_file(args.output):
            numpy_to_image(args.input, args.output)
        else:
            show_help_exit("Only support image->npz or npz->image")

    if len(args.compare) > 0:
        if is_numpy_file(args.input) and is_numpy_file(args.compare):
            compare_files(args.input, args.compare)
        else:
            show_help_exit("Input and compare file should be npz")
