from PyQt5.QtCore import QSizeF, QByteArray
from PyQt5.QtGui import QPageLayout, QPixmap, QPainter
from PyQt5.QtPrintSupport import QPrinter, QPrinterInfo

import pdf2image
import pdf2image.exceptions
import io


class PdfPrinterException(Exception):
    pass


class LabelInfo(object):

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.margin_top = 0
        self.margin_left = 0
        self.margin_bottom = 0
        self.margin_right = 0

    def set_margins(self, left, top, right, bottom):
        self.margin_top = top
        self.margin_left = left
        self.margin_bottom = bottom
        self.margin_right = right


class PdfPrinter(QPrinter):

    def __init__(self, printer_info: QPrinterInfo = None):
        super().__init__(printer_info)
        self.x_shift = 0
        self.y_shift = 0

    def print_pdf(self, label_data):
        try:
            pages = pdf2image.convert_from_bytes(label_data, self.resolution())
            img_bytes = io.BytesIO()
            pages[0].save(img_bytes, format='JPEG')
            img_bytes = img_bytes.getvalue()

            pixmap = QPixmap()
            pixmap.loadFromData(QByteArray(img_bytes), format='JPEG')

            painter = QPainter()
            painter.begin(self)
            painter.drawPixmap(self.x_shift, self.y_shift, pixmap)
            painter.end()

        except pdf2image.exceptions.PDFInfoNotInstalledError as e:
            raise PdfPrinterException(str(e))

    def set_shift(self, x_shift: int, y_shift: int):
        self.x_shift = x_shift
        self.y_shift = y_shift
