from PIL import Image, ImageTk
from PyPDF2 import PdfFileMerger, PdfFileReader, PdfFileWriter
import imutils

import io
import pdfkit
import base64


def convertNotesToPdf(notesList, fname):
    merger = PdfFileMerger()
    output = PdfFileWriter()
    for i in range(0, len(notesList), 3):
        html = _setupTable()
        for image, notes in notesList[i:i + 3 if i + 3 < len(notesList) else len(notesList)]:
            html += _addTableRow(image, notes)
        html += _finishTable()

        config = pdfkit.configuration(wkhtmltopdf='C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe')
        pdfBytes = pdfkit.from_string(html, False, configuration=config)
        pdfByteStream = io.BytesIO(pdfBytes)
        pfr = PdfFileReader(pdfByteStream)
        output.addPage(pfr.getPage(0))

    outputStream = open(fname, "wb")
    output.write(outputStream)
    outputStream.close()

    print("Finished saving PDF")


def convertNotesToHtml(notesList, fname):
    html = _setupTable()
    for image, notes in notesList:
        html += _addTableRow(image, notes)

    html += _finishTable()

    with open('test.html', 'w') as f:
        f.write(html)


def _ImageToHTMLBase64Image(image):
    b = io.BytesIO()
    image.save(b, 'JPEG')
    image_bytes = b.getvalue()
    b64 = base64.b64encode(image_bytes)
    return "<img src='data:image/png;base64,{0}'>".format(str(b64)[2:-1])


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
    
    th {
        width: 50%;
    }
    
    tr:nth-child(even) {
        background-color: #eeeeee;
    }
    
    img {
        max-width: 500px;
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
