from PyQt5 import uic, QtWidgets, QtCore
from PyQt5.QtPrintSupport import QPrinterInfo, QPrinter
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import QSizeF, QByteArray
from PyQt5.QtGui import QPainter, QPixmap, QPageLayout

import re

from MSApi.MSApi import MSApi, MSApiException

from PdfPrinter import PdfPrinter, PdfPrinterException


class PrintLabelException(Exception):
    pass


class LabelFormat(object):
    str_rx = re.compile(r'(\d+)x(\d+) +\((\d+),(\d+),(\d+),(\d+)\)')

    @classmethod
    def from_str(cls, string: str):
        match = cls.str_rx.match(string)
        if not match:
            raise PrintLabelException("Label format string not match")

        label_format = LabelFormat(int(match.group(1)), int(match.group(2)))
        label_format.set_margins(int(match.group(3)),
                                 int(match.group(4)),
                                 int(match.group(5)),
                                 int(match.group(6)))
        return label_format

    def __init__(self, width=0, height=0):
        self.width = width
        self.height = height
        self.margin_left = 0
        self.margin_top = 0
        self.margin_right = 0
        self.margin_bottom = 0

    def __str__(self):
        return f"{self.width}x{self.height} ({self.margin_left},{self.margin_top},{self.margin_right},{self.margin_bottom})"

    def set_margins(self, left, top, right, bottom):
        self.margin_left = left
        self.margin_top = top
        self.margin_right = right
        self.margin_bottom = bottom



class MainWindow(QMainWindow):

    def __error(self, err):
        QtWidgets.QMessageBox.critical(self, "Error", str(err))

    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi("mainwindow.ui", self)

        self.__printer = None

        self.btnPrint.clicked.connect(self.__onBtnPrint_clicked)
        self.lineFilter.textChanged.connect(self.__onLineFilter_textChanged)
        self.spinCount.valueChanged.connect(self.__onSpinCount_valueChanged)
        self.comboLabelSize.currentIndexChanged.connect(self.__onComboLabelSize_currentIndexChanged)

        self.__products = []
        for product in MSApi.gen_products():
            self.listProducts.addItem(product.get_name())
            self.__products.append(product)

        for template in MSApi.gen_customtemplates():
            self.comboLabelFormat.addItem(template.get_name(), template)

        self.__organization = next(MSApi.gen_organizations(), None)
        if self.__organization is None:
            raise PrintLabelException("Could not find organization")

    def set_printer(self, printer_name):
        if printer_name is None:
            printer_name = QPrinterInfo.defaultPrinterName()
        printer_info = QPrinterInfo.printerInfo(printer_name)
        if printer_info.isNull():
            raise PrintLabelException(f"{printer_name} printer is not valid")

        self.__printer = PdfPrinter(printer_info)
        pass

    def set_label_formats(self, sizes: [LabelFormat]):
        for size in sizes:
            self.comboLabelSize.addItem(str(size), size)

    @QtCore.pyqtSlot()
    def __onSpinCount_valueChanged(self):
        self.__printer.setCopyCount(self.spinCount.value())

    @QtCore.pyqtSlot()
    def __onBtnPrint_clicked(self):
        try:
            if self.__printer is None:
                raise PrintLabelException("Printer not initialised")

            product_items = self.listProducts.selectedItems()
            if len(product_items) == 0:
                raise PrintLabelException("Product not selected")
            product = self.__products[self.listProducts.row(product_items[0])]

            label_data = MSApi.load_label(product, self.__organization, self.comboLabelFormat.currentData())

            self.__printer.print_pdf(label_data)

        except MSApiException as e:
            self.__error(e)
        except PdfPrinterException as e:
            self.__error(e)

    @QtCore.pyqtSlot()
    def __onLineFilter_textChanged(self):
        new_string = self.lineFilter.text().lower()
        for i in range(self.listProducts.count()):
            item = self.listProducts.item(i)
            if new_string in item.text().lower():
                item.setHidden(False)
            else:
                item.setHidden(True)

    @QtCore.pyqtSlot()
    def __onComboLabelSize_currentIndexChanged(self):
        lf: LabelFormat = self.comboLabelSize.currentData()
        if self.__printer is None:
            raise PrintLabelException("Printer not initialised")
        self.__printer.setPageSizeMM(QSizeF(lf.width, lf.height))
        self.__printer.setPageMargins(lf.margin_left,
                                      lf.margin_top,
                                      lf.margin_right,
                                      lf.margin_bottom,
                                      QPrinter.Millimeter)
