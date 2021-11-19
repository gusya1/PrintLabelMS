import configparser
import threading

from PyQt5 import uic, QtWidgets, QtCore
from PyQt5.QtPrintSupport import QPrinterInfo, QPrinter
from PyQt5.QtWidgets import QMainWindow, QProgressDialog
from PyQt5.QtCore import QSizeF
from typing import Optional

import re

from MSApi.MSApi import MSApi, MSApiException
from MSApi import Assortment
from MSApi import Organization

from PdfPrinter import PdfPrinter, PdfPrinterException

from ui.mainwindow_ui import Ui_MainWindow

class PrintLabelException(Exception):
    pass


class LabelFormat(object):
    str_rx = re.compile(r'(\d+)x(\d+) +\((-?\d+),(-?\d+)\) ([LP])')

    @classmethod
    def from_str(cls, string: str):
        match = cls.str_rx.match(string)
        if not match:
            raise PrintLabelException("Label format string not match")

        label_format = LabelFormat(int(match.group(1)), int(match.group(2)))
        label_format.x_shift = int(match.group(3))
        label_format.y_shift = int(match.group(4))
        if match.group(5) == "P":
            label_format.orientation = QPrinter.Orientation.Portrait
        else:
            label_format.orientation = QPrinter.Orientation.Landscape
        return label_format

    def __init__(self, width=0, height=0):
        self.width = width
        self.height = height
        self.x_shift = 0
        self.y_shift = 0
        self.orientation = QPrinter.Orientation.Portrait

    def __str__(self):
        if self.orientation == QPrinter.Orientation.Portrait:
            orientation_str = "P"
        else:
            orientation_str = "L"
        return f"{self.width}x{self.height} ({self.x_shift},{self.y_shift}) {orientation_str}"


class MainWindow(QMainWindow):

    progress_changed = QtCore.pyqtSignal(str, int)

    def __error(self, err):
        QtWidgets.QMessageBox.critical(None, "Error", str(err))

    def __init__(self, config_path, parent=None):
        super().__init__(parent)

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.__printer: Optional[PdfPrinter] = None
        self.read_config(config_path)

        self.ui.btnPrint.clicked.connect(self.__onBtnPrint_clicked)
        self.ui.lineFilter.textChanged.connect(self.__onLineFilter_textChanged)
        self.ui.spinCount.valueChanged.connect(self.__onSpinCount_valueChanged)
        self.ui.comboLabelSize.currentIndexChanged.connect(self.__onComboLabelSize_currentIndexChanged)


        # self.progress_changed.connect()

        self.__onComboLabelSize_currentIndexChanged()

        self.__products = []
        for assort in Assortment.gen_list():
            obj = MSApi.get_object_by_json(assort.get_json())(assort.get_json())
            self.ui.listProducts.addItem(obj.get_name())
            self.__products.append(obj)

        for template in Assortment.gen_customtemplates():
            self.ui.comboLabelFormat.addItem(template.get_name(), template)

        self.__organization = next(Organization.gen_list(), None)
        if self.__organization is None:
            raise PrintLabelException("Could not find organization")

    def read_config(self, config_path):
        config = configparser.ConfigParser()
        config.read(config_path, encoding="utf-8")

        MSApi.set_access_token(config['moy_sklad']['token'])

        sizes = []
        for size_str in config['printer']['sizes'].split('\n'):
            if not size_str:
                continue
            lf = LabelFormat.from_str(size_str)
            self.ui.comboLabelSize.addItem(str(lf), lf)

        self.set_printer(config['printer']['name'])
        self.set_resolution(int(config['printer']['resolution']))

    def set_printer(self, printer_name):
        if printer_name is None:
            printer_name = QPrinterInfo.defaultPrinterName()
        printer_info = QPrinterInfo.printerInfo(printer_name)
        if printer_info.isNull():
            raise PrintLabelException(f"{printer_name} printer is not valid")

        self.__printer = PdfPrinter(printer_info)

    def set_resolution(self, resolution: int):
        if self.__printer is None:
            raise PrintLabelException("Printer not initialised")
        self.__printer.setResolution(resolution)

    @QtCore.pyqtSlot()
    def __onSpinCount_valueChanged(self):
        self.__printer.setCopyCount(self.ui.spinCount.value())

    def __print_label(self):
        try:
            self.progress_changed.connect(self.__change_progress)
            if self.__printer is None:
                raise PrintLabelException("Printer not initialised")

            product_items = self.ui.listProducts.selectedItems()
            if len(product_items) == 0:
                raise PrintLabelException("Product not selected")
            product = self.__products[self.ui.listProducts.row(product_items[0])]

            self.progress_changed.emit("Label loading...", 1)
            label_data = product.request_label(self.__organization,
                                               self.ui.comboLabelFormat.currentData(),
                                               verify=True)

            self.progress_changed.emit("Printing...", 2)
            self.__printer.print_pdf(label_data)

        except MSApiException as e:
            self.__error(e)
        except PdfPrinterException as e:
            self.__error(e)
        except PrintLabelException as e:
            self.__error(e)
        except Exception as e:
            self.__error(e)

        self.progress_changed.emit("Success", 3)

    @QtCore.pyqtSlot(str, int)
    def __change_progress(self, message, value):
        self.progress_dialog.setLabelText(message)
        self.progress_dialog.setValue(value)

    @QtCore.pyqtSlot()
    def __onBtnPrint_clicked(self):
        self.progress_dialog = QProgressDialog("Printing", None, 0, 3)
        self.progress_dialog.setAutoClose(True)
        thread = threading.Thread(target=self.__print_label)
        thread.start()
        self.progress_dialog.exec_()
        thread.join()
        # self.__print_label(progress)

    @QtCore.pyqtSlot()
    def __onLineFilter_textChanged(self):
        new_string = self.ui.lineFilter.text().lower()
        for i in range(self.ui.listProducts.count()):
            item = self.ui.listProducts.item(i)
            if new_string in item.text().lower():
                item.setHidden(False)
            else:
                item.setHidden(True)

    @QtCore.pyqtSlot()
    def __onComboLabelSize_currentIndexChanged(self):
        lf: LabelFormat = self.ui.comboLabelSize.currentData()
        if self.__printer is None:
            raise PrintLabelException("Printer not initialised")
        self.__printer.setPageSizeMM(QSizeF(lf.width, lf.height))
        resolution = self.__printer.resolution()
        self.__printer.set_shift(int(lf.x_shift*resolution/1000),
                                 int(lf.y_shift*resolution/1000))
        self.__printer.setOrientation(lf.orientation)
