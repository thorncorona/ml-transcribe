# Test Code for Tkinter with threads
import tkinter as Tk
import multiprocessing
from queue import *
import time
from ImageProcessor import ImageProcessor
from PIL import Image, ImageTk
import imutils

class GuiApp(object):
    def __init__(self, imageQueue):
        self.root = Tk.Tk()
        self.root.geometry('1366x768')
        self.canvas = Tk.Canvas(width=1366, height=768)
        self.canvas.pack(expand=Tk.YES, padx=0, pady=0)
        self.root.after(50, self.CheckQueuePoll, imageQueue)

    def CheckQueuePoll(self, c_queue):
        try:
            queue_item = c_queue.get(0)

            if queue_item is not None:
                warped_image, contoured_image = queue_item

                if warped_image is None:
                    return

                stream_img = warped_image
                stream_img = imutils.resize(stream_img, height=self.canvas.winfo_height())

                stream_img = Image.fromarray(stream_img)
                stream_img = ImageTk.PhotoImage(stream_img)

                self.canvas.create_image(0, 0, image=stream_img)
                # self.canvas.create_rectangle(50, 0, 100, 50, fill='red')
                # print('Canvas', self.canvas.winfo_width(), self.canvas.winfo_height())

        except Empty:
            pass
        finally:
            self.root.after(100, self.CheckQueuePoll, c_queue)


def processImages(imageQueue):
    img_proc = ImageProcessor(FPS=30, rolling_avg=15)

    while True:
        if imageQueue.empty():
            img_proc.capture_next_frame()
            imageQueue.put((img_proc.get_warped_image(),
                            img_proc.get_contoured_image()))


if __name__ == '__main__':
    # Queue which will be used for storing Data

    imageQueue = multiprocessing.Queue()
    imageQueue.cancel_join_thread()
    gui = GuiApp(imageQueue)

    t2 = multiprocessing.Process(target=processImages, args=(imageQueue,))
    t2.start()

    gui.root.mainloop()

    t2.terminate()
