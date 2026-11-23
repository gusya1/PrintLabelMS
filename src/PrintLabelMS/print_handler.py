from PyQt5.QtCore import QByteArray, QSizeF, Qt
from PyQt5.QtGui import QPixmap, QPainter, QPen
from PyQt5.QtPrintSupport import QPrinterInfo, QPrinter

from pdf_to_image_converter.converter import Converter, ConvertError

import config


CALIBRATION_LINE_WIDTH_MM = 0.3


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


def mm_to_device_pixels(value_mm, resolution):
    """
    Миллиметры в device pixels при заданном разрешении принтера.

    QPainter на QPrinter работает в точках (device pixels) при разрешении
    из setResolution; 1 дюйм = 25.4 мм.
    """
    return round(value_mm * resolution / 25.4)


def draw_calibration(painter, width_px, height_px, line_width_px):
    """
    Калибровочный эталон: рамка по границам устройства и две диагонали.

    Линия толщиной line_width_px укладывается внутрь рамки, поэтому
    отступ от краёв — line_width_px // 2.
    """
    inset = line_width_px // 2
    painter.setPen(QPen(Qt.black, line_width_px))
    painter.drawRect(inset, inset, width_px - 2 * inset, height_px - 2 * inset)
    painter.drawLine(inset, inset, width_px - inset, height_px - inset)
    painter.drawLine(width_px - inset, inset, inset, height_px - inset)


class PrintHandler:
    def __init__(self, printer_name, resolution, converter: Converter):
        self.__width_offset = 0
        self.__height_offset = 0
        self.__resolution = resolution
        self.__printer = init_printer(printer_name, self.__resolution)
        self.converter = converter

    def set_width_offset(self, width_offset):
        self.__width_offset = mm_to_device_pixels(width_offset, self.__resolution)

    def set_height_offset(self, height_offset):
        self.__height_offset = mm_to_device_pixels(height_offset, self.__resolution)

    def set_page_size(self, width, height):
        self.__printer.setPageSizeMM(QSizeF(width, height))

    def set_orientation(self, orientation):
        self.__printer.setOrientation(get_qt_orientation(orientation))

    def set_copy_count(self, count: int):
        self.__printer.setCopyCount(count)

    def print_pdf(self, pdf_data):
        try:
            jpeg_data = self.converter.convert_pdf_to_jpeg(pdf_data, self.__resolution)

            pixmap = QPixmap()
            pixmap.loadFromData(QByteArray(jpeg_data), format='JPEG')
            if pixmap.isNull():
                raise RuntimeError("Не удалось загрузить JPEG-изображение этикетки")

            painter = QPainter()
            if not painter.begin(self.__printer):
                raise RuntimeError("Не удалось инициализировать принтер для печати")
            painter.drawPixmap(self.__width_offset, self.__height_offset, pixmap)
            painter.end()

        except ConvertError as e:
            raise RuntimeError(str(e))

    def print_calibration(self, width_mm, height_mm):
        """Печатает калибровочный эталон текущего формата этикетки."""
        width_px = mm_to_device_pixels(width_mm, self.__resolution)
        height_px = mm_to_device_pixels(height_mm, self.__resolution)
        line_width_px = max(1, mm_to_device_pixels(CALIBRATION_LINE_WIDTH_MM, self.__resolution))

        painter = QPainter()
        if not painter.begin(self.__printer):
            raise RuntimeError("Не удалось инициализировать принтер для печати")
        try:
            painter.translate(self.__width_offset, self.__height_offset)
            draw_calibration(painter, width_px, height_px, line_width_px)
        finally:
            painter.end()
