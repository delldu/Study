# coding=utf-8
#
# /************************************************************************************
# ***
# ***    File Author: Dell, Sat Oct 26 03:12:22 CST 2019
# ***
# ************************************************************************************/
#

import math
import argparse
from PIL import Image, ImageChops


def diff(args):
    """
    Calculate the difference between two images.
    """

    if not args.mode == "RGBA":
        args.mode = "RGB"

    im1 = Image.open(args.first).convert(args.mode)
    im2 = Image.open(args.second).convert(args.mode)

    # Generate diff image in memory.
    diff_img = ImageChops.difference(im1, im2)

    r_cnt, g_cnt, b_cnt = 0, 0, 0
    r_psnr, g_psnr, b_psnr = 0.000001, 0.000001, 0.000001
    for y in range(diff_img.height):
        for x in range(diff_img.width):
            if args.mode == "RGBA":
                (r, g, b, a) = diff_img.getpixel((x, y))
            else:
                (r, g, b) = diff_img.getpixel((x, y))
            r_psnr = r_psnr + r * r
            g_psnr = g_psnr + g * g
            b_psnr = b_psnr + b * b
            if r > args.threshold:
                r = 255
                r_cnt = r_cnt + 1
            else:
                r = 0
            if g > args.threshold:
                g = 255
                g_cnt = g_cnt + 1
            else:
                g = 0
            if b > args.threshold:
                b = 255
                b_cnt = b_cnt + 1
            else:
                b = 0
            if args.mode == "RGBA":
                diff_img.putpixel((x, y), (r, g, b, a))
            else:
                diff_img.putpixel((x, y), (r, g, b))

    r_psnr = r_psnr / (diff_img.width * diff_img.height)
    g_psnr = g_psnr / (diff_img.width * diff_img.height)
    b_psnr = b_psnr / (diff_img.width * diff_img.height)
    r_psnr = 10 * math.log10(255.0 * 255.0 / r_psnr)
    g_psnr = 10 * math.log10(255.0 * 255.0 / g_psnr)
    b_psnr = 10 * math.log10(255.0 * 255.0 / b_psnr)

    print("Threshold:", args.threshold)
    print("Count: ", "R = ", r_cnt, ", G = ", g_cnt, ", B = ", b_cnt)

    r_cnt = r_cnt / (diff_img.width * diff_img.height)
    g_cnt = g_cnt / (diff_img.width * diff_img.height)
    b_cnt = b_cnt / (diff_img.width * diff_img.height)
    print("Count Ratio:", "R = ", r_cnt, ", G = ", g_cnt, ", B = ", b_cnt)

    print("PSNR : ", "R = ", r_psnr, ", G = ", g_psnr, ", B = ", b_psnr)

    if "." not in args.output:
        extension = "png"
    else:
        extension = args.output.split(".")[-1]
    if extension in ("jpg", "jpeg"):
        # For some reason, save() thinks "jpg" is invalid
        # This doesn't affect the image's saved filename
        extension = "jpeg"
        diff_img = diff_img.convert("RGB")
    diff_img.save(args.output, extension)

    im1.show()
    im2.show()
    diff_img.show()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Compare two images')
    parser.add_argument("-a", "--first", help="first image", required=True)
    parser.add_argument("-b", "--second", help="second image", required=True)
    parser.add_argument("-o",
                        "--output",
                        help="output image, defaut: output.png",
                        type=str,
                        default="output.png")
    parser.add_argument("-t",
                        "--threshold",
                        help="Threshold, default: 64.0",
                        type=float,
                        default=64.0)
    parser.add_argument("-m",
                        "--mode",
                        help="color mode, default: RGB, option RGBA",
                        type=str,
                        default="RGB")
    args = parser.parse_args()

    diff(args)
