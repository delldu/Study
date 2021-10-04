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

def file_name_parse(filename):
    """return file base, ext"""
    return os.path.splitext(os.path.basename(filename))[0:2]

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

def load_zip_file(afile):
    try:
        data = np.load(afile)
        return data
    except IOError as ex:
        raise Exception("Error loading file: %s" % ex)

def image_to_numpy(image_file, normalize=False):
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
    return numpy_data

def numpy_to_image(numpy_data, image_file):
    # numpy_data.shape -- (1, 3, 348, 348)
    numpy_data = np.squeeze(numpy_data, axis=0)
    if isinstance(numpy_data.shape, tuple) and len(numpy_data.shape) == 3 and numpy_data.shape[0] in [1, 3]:
        image_data = np.transpose(numpy_data, (1, 2, 0))    # CxHxW --> HxWxC
        image_data = image_data * 255
        image = Image.fromarray(image_data.astype('uint8'))
        image.save(image_file)
        return True
    return False

def compare_dict_data(dict1, dict2):
    for k, v in dict1.items():
        np.testing.assert_allclose(v, dict2[k], rtol=1e-03, atol=1e-03)

    for k, v in dict2.items():
        np.testing.assert_allclose(dict1[k], v, rtol=1e-03, atol=1e-03)

def create_afile(afile, files, normalize):
    zip_dict = {}
    for file in files:
        if not is_image_file(file):
            print(f"File {file} is not image, skip.")
            continue
        base, ext = file_name_parse(file)
        zip_dict[base] = image_to_numpy(file, normalize)
    np.savez(afile, **zip_dict)


def list_afile(afile):
    zip_dict = load_zip_file(afile)
    for k, v in zip_dict.items():
        print(k, "=", v.shape)

def extract_afile(afile, directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

    zip_dict = load_zip_file(afile)
    for k, v in zip_dict.items():
        image_file = f"{directory}/{k}.png"
        if not numpy_to_image(v, image_file):
            print(f"Could not convert {k} to image, skip ...")

def compare_afiles(afile, files):
    std_dict = load_zip_file(afile)

    for file in files:
        print(f"Start checking {file} ...")
        cmp_dict = load_zip_file(file)
        compare_dict_data(std_dict, cmp_dict)
    print("OK, almost equal.")

if __name__ == "__main__":
    """
    tvmd -- co-worker of tvmc
    """
    tvmd_description = "tvmd compress image files with npz format, like 'tar'"
    tvmd_examples = '''
    Examples:
        tvmd -c file.npz a.png b.png
        tvmd -t file.npz
        tvmd -x file.npz -C output
        tvmd -d file1.npz file2.npz
    '''

    parser = argparse.ArgumentParser(
        description=tvmd_description,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("FILES", type=str, nargs='*', help="image files")
    parser.add_argument("-c", "--create", type=str, help="create a new archive")
    parser.add_argument("-n", "--normal", help="imagenet normal for create option", action="store_true")
    parser.add_argument("-t", "--list", type=str, help="list the contents of an archive")
    parser.add_argument("-x", "--extract", type=str, help="extract files from an archive")
    parser.add_argument("-C", "--directory", metavar="DIR", type=str, default="output", help="change to directory DIR")
    parser.add_argument("-d", "--diff", type=str, help="find differences between archive files")

    args = parser.parse_args()

    if args.create:
        create_afile(args.create, args.FILES, args.normal)
    elif args.list:
        list_afile(args.list)
    elif args.extract:
        extract_afile(args.extract, args.directory)
    elif args.diff:
        compare_afiles(args.diff, args.FILES)
    else:
        parser.print_help()
        print()
        print(tvmd_examples.strip().replace(" "*8, " "*4))
