from PIL import Image, ImageTk
import imutils

import pdfkit
import base64


def convertNotesToPdf(notesList, fname):
    html = _setupTable()
    for image, notes in notesList:
        html += _addTableRow(image, notes)

    html += _finishTable()

    return pdfkit.from_string(html, fname)


def _ImageToHTMLBase64Image(image):
    byteEncoding = Image.toBytes(image, encoder_name='jpg')
    b64 = base64.b64encode(byteEncoding)
    return "<img src='data:image/png;base64,{0}'".format(b64)


def _addTableRow(image, notes):
    return """<tr>
    <th>{0}</th>
    <th>{1}</th>
  </tr>""".format(_ImageToHTMLBase64Image(image), notes)


def _setupTable():
    return """
    <!DOCTYPE html>
    <html>
    <head>
    <style>
    table {
        font-family: arial, sans-serif;
        border-collapse: collapse;
        width: 100%;
    }
    
    td, th {
        border: 1px solid #dddddd;
        text-align: left;
        padding: 8px;
    }
    
    tr:nth-child(even) {
        background-color: #eeeeee;
    }
    
    img {
        max-width: 1000px;
    }
    </style>
    </head>
    <body>
    <table>
    """


def _finishTable():
    return """
            </table>
            </body>
            </html>"""
