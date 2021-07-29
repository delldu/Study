# coding=utf-8

# /************************************************************************************
# ***
# ***    File Author: Dell, 2018年 12月 17日 星期一 16:33:18 CST
# ***
# ************************************************************************************/

import sys
import cv2
import numpy as np
import matplotlib.pyplot as plt


def image_cut(image_filename):
    img = cv2.imread(image_filename)
    img = cv2.resize(img, (320, 480))

    plt.subplot(1, 2, 1)
    plt.title("original image ")
    plt.xticks([])
    plt.yticks([])
    plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

    mask = np.zeros((img.shape[:2]), np.uint8)
    bgmodel = np.zeros((1, 65), np.float64)
    fgmodel = np.zeros((1, 65), np.float64)
    rect = (10, 10, img.shape[1] - 10, img.shape[0] - 10)

    cv2.grabCut(img, mask, rect, bgmodel, fgmodel, 32, cv2.GC_INIT_WITH_RECT)

    # 0 -- cv2.GC_BGD, 1 -- cv2.GC_FGD, 2 -- cv2.GC_PR_BGD, 3 -- cv2.GC_PR_FGD
    mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype("uint8")

    img = img * mask2[:, :, np.newaxis]

    plt.subplot(1, 2, 2)
    plt.title("target image")
    plt.xticks([])
    plt.yticks([])
    plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

    plt.show()


if __name__ == "__main__":
    image_cut(sys.argv[1])
