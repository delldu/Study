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
        return False

def is_npz_file(filename):
    return file_name_ext(filename) == ".npz"

def image_to_npz(image_file, npz_file, normalize=False):
    print(f"compressing {image_file} to {npz_file} ...")

def npz_to_image(npz_file, image_file, normalize=False):
    print(f"Decompressing {npz_file} to {image_file} ...")

def compare_files(npz_file1, npz_file2):
    print("Compare file {npz_file1} and {npz_file2} ...")

if __name__ == "__main__":
    """
    tvmd -- coworker of tvmc
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
        if is_image_file(args.input) and is_npz_file(args.output):
            image_to_npz(args.input, args.output, args.normal)
        elif is_npz_file(args.input) and is_image_file(args.output):
            npz_to_image(args.input, args.output, args.normal)
        else:
            show_help_exit("Only support image->npz or npz->image")

    if len(args.compare) > 0:
        assert os.path.exists(args.compare), f"File {args.compare} not exist."
        if is_npz_file(args.input) and is_npz_file(args.compare):
            compare_files(args.input, args.compare)
        else:
            show_help_exit("Only support compare npz files")
