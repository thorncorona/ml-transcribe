from PIL import Image, ImageTk
import imutils

import pdfkit
import base64

def convertNotesToPdf(notesList):

def _ImageToHTMLBase64Image(image):
    byteEncoding = Image.toBytes(image, encoder_name='jpg')
    b64 = base64.b64encode(byteEncoding)
    return "<img src='data:image/png;base64,{0}" % b64
