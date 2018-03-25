# Test Code for Tkinter with threads
import tkinter as tk
import multiprocessing
from queue import *
import time
from ImageProcessor import ImageProcessor
from PIL import Image, ImageTk
import imutils


class GuiApp(object):
    def __init__(self, speechQueue, imageQueue):
        self.root = tk.Tk()
        self.root.bind('<space>', self.bindToSaveSlide)

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
        self.imageLabel = tk.Label(self.root, image=img, height=500)
        self.imageLabel.pack(side="top", fill="both", expand="yes")
        # and add the image holder  as the top (first) component of tb split pane
        self.topBottomSplitPane.add(self.imageLabel)

        # 2. add a textbox as the bottom (second) component of the above tb split pane
        self.text_bottomPlaceHolder = tk.Label(self.topBottomSplitPane, text="BOTTOM")
        self.topBottomSplitPane.add(self.text_bottomPlaceHolder)

        # 3. add a text box in the created split pane
        self.text_wid = tk.Text(self.leftRightSplitPane)
        self.leftRightSplitPane.add(self.text_wid)

        self.root.after(100, self.check_speech_queue_poll, speechQueue)
        self.root.after(50, self.check_image_queue_poll, imageQueue)

        self.slide = None
        self.notes = ""
        self.savedNotes = []

    def check_image_queue_poll(self, c_queue):
        try:
            queue_item = c_queue.get(0)

            if queue_item is not None:
                warped_image, contoured_image = queue_item

                if warped_image is None:
                    return

                self.slide = warped_image

                stream_img = imutils.resize(warped_image, height=self.imageLabel.winfo_height())
                stream_img = Image.fromarray(stream_img)
                stream_img = ImageTk.PhotoImage(stream_img)

                self.imageLabel.configure(image=stream_img)
                self.imageLabel.image = stream_img  # need to prevent garbage collecting
        except Empty:
            pass
        finally:
            self.root.after(100, self.check_image_queue_poll, c_queue)

    def check_speech_queue_poll(self, speechQueue):
        try:
            queue_item = speechQueue.get(0)
            self.notes += queue_item

            self.text_wid.insert('end', queue_item)
        except Empty:
            pass
        finally:
            self.root.after(100, self.check_speech_queue_poll, speechQueue)

    def bindToSaveSlide(self, event):
        self.savedNotes.append((self.slide, self.notes))
        print("Saved")


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


def processSpeech(speechQueue):
    pass
    # language_code = 'en-US'  # a BCP-47 language tag

    # client = speech.SpeechClient()
    # config = types.RecognitionConfig(
    #     encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
    #     sample_rate_hertz=RATE,
    #     language_code=language_code)
    # streaming_config = types.StreamingRecognitionConfig(
    #     config=config,
    #     interim_results=True)
    #
    # while True:
    #     try:
    #         print("restarting")
    #         streamAudio(client, config, streaming_config, q)
    #     except:
    #         print("error occured ")
    #         pass


def processImages(imageQueue):
    img_proc = ImageProcessor(FPS=30, rolling_avg=15)

    while True:
        if imageQueue.empty():
            img_proc.capture_next_frame()
            imageQueue.put((img_proc.get_warped_image(),
                            img_proc.get_contoured_image()))


if __name__ == '__main__':
    # Queue which will be used for storing Data

    speechQueue = multiprocessing.Queue()
    speechQueue.cancel_join_thread()

    imageQueue = multiprocessing.Queue()
    imageQueue.cancel_join_thread()
    gui = GuiApp(speechQueue, imageQueue)

    t1 = multiprocessing.Process(target=processSpeech, args=(speechQueue,))
    t1.start()

    t2 = multiprocessing.Process(target=processImages, args=(imageQueue,))
    t2.start()

    gui.root.mainloop()

    t1.terminate()
    t2.terminate()
