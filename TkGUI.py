import tkinter as tk
from tkinter import filedialog as fdialog

from PIL import Image, ImageTk
import imutils

import multiprocessing
from queue import *

from GoogleSpeechStream import *
from ImageProcessor import *
from NotesToPdf import convertNotesToPdf
import imutils
import time

# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms


class GuiApp(object):
    def __init__(self, textQueue, imageQueue, imSetQueue):
        self.root = tk.Tk()
        self.root.bind('<F1>', self.bindToSaveSlide)
        self.root.bind('<F2>', self.bindToLockSlide)
        self.root.bind('<F3>', self.bindToLockFrame)

        self.slide = None
        self.notes = ""
        self.savedNotes = []
        self.STARTED = False
        self.lockSlide = False
        self.lockFrame = False
        self.imSetQueue = imSetQueue

        # First we set the title of the entire frame
        self.root.title("AutoDoc - (F1) Save notes, (F2) Lock Slide Image, (F3), Lock view")

        #### first create GUI component holders : PaneWindow

        # 1. create a left right split pane
        self.leftRightSplitPane = tk.PanedWindow()
        self.leftRightSplitPane.pack(fill="both", expand="yes")

        # 2.  create a top bottom split pane
        self.topBottomSplitPane = tk.PanedWindow(orient=tk.VERTICAL)

        # 3.  add the created tb split pane as a component of the above lr split pane
        self.leftRightSplitPane.add(self.topBottomSplitPane)

        #### then create and add the GUI components in the PaneWindow
        # 1. add the image holder GUI component
        img = ImageTk.PhotoImage(Image.open("PlaceHolderImage.jpg"))
        self.imagebox = tk.Label(self.root, image=img, height=600, width=800)
        self.imagebox.pack(side="top", fill="both", expand="yes")
        # and add the image holder  as the top (first) component of tb split pane
        self.topBottomSplitPane.add(self.imagebox)

        # 2. add a textbox as the bottom (second) component of the above tb split pa
        self.startButton = tk.Button(self.root, bg="green", fg="black", text="START", command=self.startRecord)
        self.stopButton = tk.Button(self.root, bg="red", fg="black", text="STOP", command=self.stopRecord)
        self.screenShot = tk.Button(self.root, bg="blue", fg="white", text="SCREENSHOT (F1)", command=self.saveSlide)
        self.saveAsPDF = tk.Button(self.root, bg="#ff3330", fg="white", text="Save as PDF", command=self.savePDF)
        self.topBottomSplitPane.add(self.startButton)
        self.topBottomSplitPane.add(self.stopButton)
        self.topBottomSplitPane.add(self.screenShot)
        self.topBottomSplitPane.add(self.saveAsPDF)

        # 4. add a text box in the created split pane
        self.text_wid = tk.Text(self.leftRightSplitPane)
        self.leftRightSplitPane.add(self.text_wid)

        self.root.after(100, self.check_speech_queue_poll, textQueue)
        self.root.after(50, self.check_image_queue_poll, imageQueue)

    def check_speech_queue_poll(self, speechQueue):
        try:
            queue_item = speechQueue.get(0)

            if self.STARTED is True:
                self.notes += queue_item
                self.text_wid.insert('end', queue_item)
        except Empty:
            pass
        finally:
            self.root.after(100, self.check_speech_queue_poll, speechQueue)

    def check_image_queue_poll(self, imageQueue):
        try:
            queue_item = imageQueue.get()

            if queue_item is not None:
                warped_image, contoured_image = queue_item

                if warped_image is None or self.imagebox.winfo_height() < 50:
                    return

                stream_img = imutils.resize(warped_image, height=self.imagebox.winfo_height())
                stream_img = Image.fromarray(stream_img)
                self.slide_raw = stream_img

                stream_img = ImageTk.PhotoImage(stream_img)

                self.imagebox.configure(image=stream_img)
                self.imagebox.image = stream_img  # need to prevent garbage collecting
        except Empty:
            pass
        finally:
            self.root.after(100, self.check_image_queue_poll, imageQueue)

    def savePDF(self):
        f = fdialog.asksaveasfile(mode='w', defaultextension=".pdf")
        if f is None:  # asksaveasfile return `None` if dialog closed with "cancel".
            return
        else:
            fname = f.name
            pdf = convertNotesToPdf(self.savedNotes, fname)
            f.close()

    def bindToSaveSlide(self, event):
        self.saveSlide()

    def saveSlide(self):

        if self.slide is None:
            self.slide = self.slide_raw

        self.savedNotes.append((self.slide, self.text_wid.get("1.0", tk.END)))
        self.text_wid.delete(1.0, tk.END)
        self.slide = None
        self.notes = ""
        print("Saved")

    def bindToLockSlide(self, event):
        self.lockSlideToggle()

    def lockSlideToggle(self):
        self.lockSlide = True
        self.slide = self.slide_raw
        print("lock slide: ", self.lockSlide)

    def bindToLockFrame(self, event):
        self.lockFrameToggle()

    def lockFrameToggle(self):
        self.lockFrame = not self.lockFrame
        self.imSetQueue.put(self.lockFrame)
        print("Lock Frame: ", self.lockFrame)

    def startRecord(self):
        print("Started recording")
        self.STARTED = True

    def stopRecord(self):
        print("Stopped recording")
        self.STARTED = False


def listen_print_loop(responses, speechQueue):
    """Iterates through server responses and prints them.

    The responses passed is a generator that will block until a response
    is provided by the server.

    Each response may contain multiple results, and each result may contain
    multiple alternatives; for details, see https://goo.gl/tjCPAU.  Here we
    print only the transcription for the top alternative of the top result.

    In this case, responses are provided for interim results as well. If the
    response is an interim one, print a line feed at the end of it, to allow
    the next result to overwrite it, until the response is a final one. For the
    final one, print a newline to preserve the finalized transcription.
    """
    num_chars_printed = 0
    for response in responses:
        if not response.results:
            continue

        # The `results` list is consecutive. For streaming, we only care about
        # the first result being considered, since once it's `is_final`, it
        # moves on to considering the next utterance.
        result = response.results[0]
        if not result.alternatives:
            continue

        # Display the transcription of the top alternative.
        transcript = result.alternatives[0].transcript

        # Display interim results, but with a carriage return at the end of the
        # line, so subsequent lines will overwrite them.
        #
        # If the previous result was longer than this one, we need to print
        # some extra spaces to overwrite the previous result
        overwrite_chars = ' ' * (num_chars_printed - len(transcript))

        if not result.is_final:
            sys.stdout.write(transcript + overwrite_chars + '\r')
            sys.stdout.flush()

            num_chars_printed = len(transcript)

        else:
            speechQueue.put(transcript + overwrite_chars)
            num_chars_printed = 0


def streamAudio(client, config, streaming_config, q):
    with MicrophoneStream(RATE, CHUNK) as stream:
        audio_generator = stream.generator()
        requests = (types.StreamingRecognizeRequest(audio_content=content)
                    for content in audio_generator)

        responses = client.streaming_recognize(streaming_config, requests)

        # Now, put the transcription responses to use.
        listen_print_loop(responses, q)


def listen(speechQueue):
    pass
    language_code = 'en-US'  # a BCP-47 language tag

    client = speech.SpeechClient()
    config = types.RecognitionConfig(
        encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code=language_code)
    streaming_config = types.StreamingRecognitionConfig(
        config=config,
        interim_results=True)

    while True:
        try:
            print("restarting")
            streamAudio(client, config, streaming_config, speechQueue)
        except:
            pass


def processImages(imageQueue, imSetQueue):
    img_proc = ImageProcessor(FPS=30, rolling_avg=15)
    lockFrame = False
    while True:

        if imSetQueue.empty() is False:
            lockFrame = imSetQueue.get(0)

        if imageQueue.empty():
            img_proc.capture_next_frame(lockFrame)
            imageQueue.put((img_proc.get_warped_image(),
                            img_proc.get_contoured_image()))


def main():
    # Queue which will be used for storing Data
    imageQueue = multiprocessing.Queue()
    imageQueue.cancel_join_thread()  # or else thread that puts data will not term
    imSetQueue = multiprocessing.Queue()
    imSetQueue.cancel_join_thread()  # or else thread that puts data will not term

    speechQueue = multiprocessing.Queue()
    speechQueue.cancel_join_thread()  # or else thread that puts data will not term

    gui = GuiApp(speechQueue, imageQueue, imSetQueue)

    videoThread = multiprocessing.Process(target=processImages, args=(imageQueue, imSetQueue))
    transcribeThread = multiprocessing.Process(target=listen, args=(speechQueue,))

    videoThread.start()
    transcribeThread.start()

    gui.root.mainloop()

    videoThread.join()
    transcribeThread.join()


if __name__ == '__main__':
    main()
