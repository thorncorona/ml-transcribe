import tkinter as tk
import multiprocessing
from queue import *
import time
import pyaudio
from array import array
from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types
from GoogleSpeechStream import *
import pygubu
import imageio
from PIL import Image, ImageTk
# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms


class GuiApp(object):
    def __init__(self, q, master=None):
        self.root = master

        #self.root.resizable(width = False, height = False)

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
        imagebox = tk.Label(self.root, image=img)
        imagebox.pack(side="top", fill="both", expand="yes")
        # and add the image holder  as the top (first) component of tb split pane
        self.topBottomSplitPane.add(imagebox)

        # 2. add a textbox as the bottom (second) component of the above tb split pane
        self.text_bottomPlaceHolder = tk.Label(self.topBottomSplitPane, text="BOTTOM")
        self.topBottomSplitPane.add(self.text_bottomPlaceHolder)

        # 3. add a text box in the created split pane
        self.text_wid = tk.Text(self.leftRightSplitPane)
        self.leftRightSplitPane.add(self.text_wid)

        self.root.after(100, self.CheckQueuePoll, q)

        self.root.mainloop()
        # video_name = "PlaceHolderImage.jpg" #This will be our video file path, in this case live from the webcam
        # video = imageio.get_reader(video_name)

        # def stream(label):
        #     for image in video.iter_data():
        #         frame_image = ImageTk.PhotoImage(Image.fromarray(image))
        #         imagebox.config(image=frame_image)
        #         imagebox.image = frame_image
        # if __name__ == "__main__":
        #     root = Tk.Tk()
        #     my_label = Tk.Label(root)
        #     my_label.pack()
        #     thread = threading.Thread(target=stream, args=(my_label,))
        #     thread.daemon = 1
        #     thread.start()
        #     root.mainloop()

    def CheckQueuePoll(self, c_queue):
        try:
            imagequeue = c_queue.get(0)
            queueitem = c_queue.get(0)
            self.text_wid.insert('end', queueitem)
        except Empty:
            pass
        finally:
            self.root.after(100, self.CheckQueuePoll, c_queue)


def listen_print_loop(responses, q):
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
            q.put(transcript + overwrite_chars)
            num_chars_printed = 0


def streamAudio(client, config, streaming_config, q):
    with MicrophoneStream(RATE, CHUNK) as stream:
        audio_generator = stream.generator()
        requests = (types.StreamingRecognizeRequest(audio_content=content)
                    for content in audio_generator)

        responses = client.streaming_recognize(streaming_config, requests)

        # Now, put the transcription responses to use.
        listen_print_loop(responses, q)

def getVideoImage():...

def listen(q):
    language_code = 'en-US'  # a BCP-47 language tag

    #client = speech.SpeechClient()
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
            streamAudio(client, config, streaming_config, q)
        except:
            print("error occured ")
            pass

if __name__ == '__main__':
    # Queue which will be used for storing Data

    q = multiprocessing.Queue()
    q2 = multiprocessing.Queue()
    q.cancel_join_thread()  # or else thread that puts data will not term
    q2.cancel_join_thread()  # or else thread that puts data will not term

    root = tk.Tk()
    gui = GuiApp(q2, master=root)
    # t1 = multiprocessing.Process(target=GenerateData, args=(q,))
    # t2 = multiprocessing.Process(target=listen, args=(q2,))
    # # t1.start()
    # t2.start()

    # root.mainloop()

    # t1.join()
    #t2.join()
