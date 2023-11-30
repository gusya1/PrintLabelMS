from PyQt5.QtCore import QByteArray, QSizeF
from PyQt5.QtGui import QPixmap, QPainter
from PyQt5.QtPrintSupport import QPrinterInfo, QPrinter

from pdf2image import pdf2image
import pdf2image.exceptions

import io

import config


def convert_pdf_to_jpeg(pdf_data, resolution):
    pages = pdf2image.convert_from_bytes(pdf_data, resolution)
    img_bytes = io.BytesIO()
    pages[0].save(img_bytes, format='JPEG')
    return img_bytes.getvalue()


def init_printer(printer_name: str, resolution: int):
    printer_info = QPrinterInfo.printerInfo(printer_name)
    if printer_info.isNull():
        raise RuntimeError(f"Принтер {printer_name} не найден")
    printer = QPrinter(printer_info)
    printer.setResolution(resolution)
    return printer


def get_qt_orientation(orientation: config.Orientation):
    return {
        config.Orientation.LANDSCAPE: QPrinter.Orientation.Landscape,
        config.Orientation.PORTRAIT: QPrinter.Orientation.Portrait
    }[orientation]


class PrintHandler:
    def __init__(self, printer_name, resolution):
        self.__width_offset = 0
        self.__height_offset = 0
        self.__resolution = resolution
        self.__printer = init_printer(printer_name, self.__resolution)

    def set_width_offset(self, width_offset):
        self.__width_offset = int(width_offset * self.__resolution / 1000)

    def set_height_offset(self, height_offset):
        self.__height_offset = int(height_offset * self.__resolution / 1000)

    def set_page_size(self, width, height):
        self.__printer.setPageSizeMM(QSizeF(width, height))

    def set_orientation(self, orientation):
        self.__printer.setOrientation(get_qt_orientation(orientation))

    def set_copy_count(self, count: int):
        self.__printer.setCopyCount(count)

    def print_pdf(self, pdf_data):
        try:
            jpeg_data = convert_pdf_to_jpeg(pdf_data, self.__resolution)

            pixmap = QPixmap()
            pixmap.loadFromData(QByteArray(jpeg_data), format='JPEG')

            painter = QPainter()
            painter.begin(self.__printer)
            painter.drawPixmap(self.__width_offset, self.__height_offset, pixmap)
            painter.end()

        except pdf2image.exceptions.PDFInfoNotInstalledError as e:
            raise RuntimeError(str(e))
