import threading

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMainWindow, QProgressDialog


from MSApi.MSApi import MSApiException

from .ui.mainwindow_ui import Ui_MainWindow

from PrintLabelMS.print_handler import PrintHandler


def get_label_format_string(label_format):
    return "{}x{} ({}, {}) {}".format(label_format.width, label_format.height, label_format.width_offset,
                                      label_format.height_offset, label_format.orientation)


class MainWindow(QMainWindow):
    progress_changed = QtCore.pyqtSignal(str, int)
    error_expected = QtCore.pyqtSignal(str)


    def __init__(self, print_handler: PrintHandler, label_formats, assortment, templates, organization, parent=None):
        super().__init__(parent)

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.__print_handler = print_handler

        for label_format in label_formats:
            self.ui.comboLabelSize.addItem(get_label_format_string(label_format), label_format)

        self.__assortment = assortment
        for product in self.__assortment:
            self.ui.listProducts.addItem(product.get_name())

        for template in templates:
            self.ui.comboLabelFormat.addItem(template.get_name(), template)

        self.ui.btnPrint.clicked.connect(self.__onBtnPrint_clicked)
        self.ui.lineFilter.textChanged.connect(self.__onLineFilter_textChanged)
        self.progress_changed.connect(self.__change_progress)
        self.error_expected.connect(self.__show_error_dialog)

        self.__organization = organization

    def reset_print_settings(self):
        label_format = self.ui.comboLabelSize.currentData()
        self.__print_handler.set_page_size(label_format.width, label_format.height)
        self.__print_handler.set_width_offset(label_format.width_offset)
        self.__print_handler.set_height_offset(label_format.height_offset)
        self.__print_handler.set_orientation(label_format.orientation)
        self.__print_handler.set_copy_count(self.ui.spinCount.value())

    def __print_label(self):
        try:
            self.reset_print_settings()

            product_items = self.ui.listProducts.selectedItems()
            if len(product_items) == 0:
                raise RuntimeError("Продукт не выбран")
            product = self.__assortment[self.ui.listProducts.row(product_items[0])]

            self.progress_changed.emit("Загрузка этикетки...", 1)
            label_data = product.request_label(self.__organization,
                                               self.ui.comboLabelFormat.currentData(),
                                               verify=True)

            self.progress_changed.emit("Печать...", 2)
            self.__print_handler.print_pdf(label_data)

        except Exception as e:
            self.error_expected.emit(str(e))

        self.progress_changed.emit("Готово", 3)

    @QtCore.pyqtSlot(str, int)
    def __change_progress(self, message, value):
        self.progress_dialog.setLabelText(message)
        self.progress_dialog.setValue(value)

    @QtCore.pyqtSlot(str)
    def __show_error_dialog(self, message):
        QtWidgets.QMessageBox.warning(None, "Ошибка", str(message))

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
