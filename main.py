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

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1366)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 768)
cap.set(cv2.CAP_PROP_FPS, 15)
w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)

print(w, h)
while (True):
    # Capture frame-by-frame
    ret, image = cap.read()

    # image = cv2.flip(image, 1)

    # Our operations on the frame come here
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2YUV)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(gray, 75, 200)

    # Display the resulting frame
    cv2.imshow('frame', gray)
    # cv2.imshow('edge', edged)

    cnts = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if imutils.is_cv2() else cnts[1]
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:5]

    screenCnt = None
    # loop over the contours
    for c in cnts:
        # approximate the contour
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)

        # if our approximated contour has four points, then we
        # can assume that we have found our screen
        if len(approx) == 4:
            screenCnt = approx
            break

    if screenCnt is not None:
        contoured = copy.copy(image)
        # show the contour (outline) of the piece of paper
        cv2.drawContours(contoured, [screenCnt], -1, (0, 255, 0), 2)
        cv2.imshow("Outline", contoured)

        warped = transform.four_point_transform(image, screenCnt.reshape(4, 2))
        # warped = cv2.adaptiveThreshold(cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        #                                cv2.THRESH_BINARY, 11, 2)

        # convert the warped image to grayscale, then threshold it
        # to give it that 'black and white' paper effect

        # warped = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
        # T = threshold_local(warped, 11, offset=10, method="gaussian")
        # warped = (warped > T).astype("uint8") * 255

        cv2.imshow("Scanned", imutils.resize(warped, height=768))

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything done, release the capture
cap.release()
cv2.destroyAllWindows()
