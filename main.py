from __future__ import print_function

import numpy as np
import cv2

from skimage.filters import threshold_local
import transform

from PIL import Image
from PIL import ImageTk
import tkinter as tki
import threading
import datetime
import imutils
import cv2
import os
import copy
import numpy as np
from matplotlib import pyplot as plt

FPS = 3
cap = cv2.VideoCapture(1)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1366)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 768)
cap.set(cv2.CAP_PROP_FPS, FPS)
w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)

print(w, h)

sift = cv2.xfeatures2d.SIFT_create()

rollingsquare = []

while True:
    # Capture frame-by-frame
    ret, image = cap.read()

    # Our operations on the frame come here
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2YUV)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(gray, 75, 200)

    cnts = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if imutils.is_cv2() else cnts[1]
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:5]

    screenCnt = None
    screenRawCnt = None
    prev_warped_sm = None
    warped_sm = None
    # loop over the contours
    for c in cnts:
        # approximate the contour
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)

        # if our approximated contour has four points, then we
        # can assume that we have found our screen
        if len(approx) == 4:
            rollingsquare.append(approx)

            med = np.array(rollingsquare)

            tLx = med[:, 0, 0, 0]
            tRx = med[:, 1, 0, 0]
            bRx = med[:, 2, 0, 0]
            bLx = med[:, 3, 0, 0]

            tLy = med[:, 0, 0, 1]
            tRy = med[:, 1, 0, 1]
            bRy = med[:, 2, 0, 1]
            bLy = med[:, 3, 0, 1]

            medianFrame = np.array([[[np.median(tLx), np.median(tLy)]],
                                    [[np.median(tRx), np.median(tRy)]],
                                    [[np.median(bRx), np.median(bRy)]],
                                    [[np.median(bLx), np.median(bLy)]]]).astype(int)

            screenCnt = medianFrame
            screenRawCnt = approx

            if len(rollingsquare) > FPS:
                rollingsquare.pop(0)
            break

    if screenCnt is not None:
        contoured = copy.copy(image)

        # contouredKp = fast.detect(gray, None)
        # cv2.drawKeypoints(contoured, contouredKp, None, (255, 0, 0), 10)
        # print("kp:", contouredKp[0])

        # show the contour (outline) of the piece of paper
        cv2.drawContours(contoured, [screenCnt], -1, (0, 255, 0), 2)
        cv2.drawContours(contoured, [screenRawCnt], -1, (0, 0, 255), 2)
        cv2.imshow("Detection", contoured)

        warped = transform.four_point_transform(image, screenCnt.reshape(4, 2))

        warped_sm = imutils.resize(warped, height=768)
        cv2.imshow("Scanned", warped_sm)

        # if warped.shape[0] > 0 and warped.shape[1] > 0:
        #     resize_w = 250
        #     resize_dim = (resize_w, int(warped.shape[0] * (resize_w * 1.0 / warped.shape[1])))
        #     warped_resize = cv2.resize(warped, resize_dim, interpolation=cv2.INTER_AREA)
        #
        #     blurred = cv2.GaussianBlur(warped_resize, (55, 55), 0)
        #     blurred = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
        #     cv2.imshow("Blurred", blurred)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()