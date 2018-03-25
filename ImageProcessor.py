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


class ImageProcessor(object):
    def __init__(self, FPS, rolling_avg, camera_input=0):
        self.FPS = FPS
        self.PRESENTATION_ROLLING_AVG = rolling_avg
        self.contoured_image = None
        self.warped_image = None

        self.cap = cap = cv2.VideoCapture(camera_input)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1366)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 768)
        cap.set(cv2.CAP_PROP_FPS, FPS)
        w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        print(w, h)

        self.presentation_rolling_frames = []

    def __del__(self):
        # When everything done, release the capture
        self.cap.release()
        cv2.destroyAllWindows()

    def capture_next_frame(self):
        ret, image = self.cap.read()

        if image is not None:
            presentation = self.edge_detect_screen(image)

            if presentation is not None:
                self.warped_image, self.contoured_img = presentation

    def edge_detect_screen(self, image):
        # Our operations on the frame come here
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2YUV)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        edged = cv2.Canny(gray, 75, 200)

        contours = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        contours = contours[0] if imutils.is_cv2() else contours[1]
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]

        averaged_screen_contours = None
        raw_screen_contours = None

        # loop over the contours
        for c in contours:
            # approximate the contour
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)

            # if our approximated contour has four points, then we
            # can assume that we have found our screen
            if len(approx) == 4:
                self.presentation_rolling_frames.append(approx)

                med = np.array(self.presentation_rolling_frames)

                # average the frames to prevent flickering of screen
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

                averaged_screen_contours = medianFrame
                raw_screen_contours = approx

                if len(self.presentation_rolling_frames) > self.PRESENTATION_ROLLING_AVG:
                    self.presentation_rolling_frames.pop(0)
                break

        if averaged_screen_contours is not None:
            contoured_img = copy.copy(image)
            cv2.drawContours(contoured_img, [averaged_screen_contours], -1, (0, 255, 0), 2)
            cv2.drawContours(contoured_img, [raw_screen_contours], -1, (0, 0, 255), 2)

            warped = transform.four_point_transform(image, averaged_screen_contours.reshape(4, 2))
            # cv2.imshow("contour", contoured_img)
            # print(averaged_screen_contours.reshape(4,2))
            return warped, contoured_img
        else:
            return None

    def get_contoured_image(self):
        if self.contoured_image is not None:
            return cv2.cvtColor(self.contoured_image, cv2.COLOR_BGR2RGB)

    def get_warped_image(self):
        if self.warped_image is not None:
            return cv2.cvtColor(self.warped_image, cv2.COLOR_BGR2RGB)
