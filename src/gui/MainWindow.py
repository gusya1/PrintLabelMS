import sys
import threading

import resources
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QMainWindow, QProgressDialog


from .ui.mainwindow_ui import Ui_MainWindow
from gui.update_service import UpdateService

from PrintLabelMS.print_handler import PrintHandler


def get_label_format_string(label_format):
    return "{}x{} ({}, {}) {}".format(label_format.width, label_format.height, label_format.width_offset,
                                      label_format.height_offset, label_format.orientation)


class MainWindow(QMainWindow):
    progress_changed = QtCore.pyqtSignal(str, int)
    error_expected = QtCore.pyqtSignal(str)

    def __init__(
        self,
        print_handler: PrintHandler,
        manager,
        label_formats,
        assortment,
        templates,
        organization,
        check_updates=True,
        parent=None,
    ):
        super().__init__(parent)

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowIcon(QtGui.QIcon(resources.get_resource_path("pictures/icon.png")))

        self.__print_handler = print_handler
        self.__manager = manager

        for label_format in label_formats:
            self.ui.comboLabelSize.addItem(get_label_format_string(label_format), label_format)

        self.__assortment = assortment
        for product in self.__assortment:
            self.ui.listProducts.addItem(product.name)

        for template in templates:
            self.ui.comboLabelFormat.addItem(template.name, template)

        self.ui.btnPrint.clicked.connect(self.__onBtnPrint_clicked)
        self.ui.lineFilter.textChanged.connect(self.__onLineFilter_textChanged)
        self.progress_changed.connect(self.__change_progress)
        self.error_expected.connect(self.__show_error_dialog)

        self.__organization = organization
        self.__printing = False
        self.progress_dialog = None
        self.__setup_update_ui(check_updates)

    def reset_print_settings(self, label_format, count):
        self.__print_handler.set_page_size(label_format.width, label_format.height)
        self.__print_handler.set_width_offset(label_format.width_offset)
        self.__print_handler.set_height_offset(label_format.height_offset)
        self.__print_handler.set_orientation(label_format.orientation)
        self.__print_handler.set_copy_count(count)

    def __collect_print_params(self):
        product_items = self.ui.listProducts.selectedItems()
        if len(product_items) == 0:
            raise RuntimeError("Продукт не выбран")
        product = self.__assortment[self.ui.listProducts.row(product_items[0])]
        label_format = self.ui.comboLabelSize.currentData()
        if label_format is None:
            raise RuntimeError("Формат этикетки не выбран")
        template = self.ui.comboLabelFormat.currentData()
        count = self.ui.spinCount.value()
        return product, label_format, template, count

    def __print_label(self, product, label_format, template, count):
        try:
            self.reset_print_settings(label_format, count)

            self.progress_changed.emit("Загрузка этикетки...", 1)
            label_data = self.__manager.request_label(product, self.__organization, template)

            self.progress_changed.emit("Печать...", 2)
            self.__print_handler.print_pdf(label_data)

        except Exception as e:
            self.error_expected.emit(str(e))
            return

        self.progress_changed.emit("Готово", 3)

    @QtCore.pyqtSlot(str, int)
    def __change_progress(self, message, value):
        self.progress_dialog.setLabelText(message)
        self.progress_dialog.setValue(value)

    @QtCore.pyqtSlot(str)
    def __show_error_dialog(self, message):
        QtWidgets.QMessageBox.warning(self, "Ошибка", str(message))

    @QtCore.pyqtSlot()
    def __onBtnPrint_clicked(self):
        try:
            product, label_format, template, count = self.__collect_print_params()
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Ошибка", str(e))
            return

        self.__printing = True
        self.progress_dialog = QProgressDialog("Печать...", None, 0, 3)
        self.progress_dialog.setAutoClose(True)
        thread = threading.Thread(target=self.__print_label, args=(product, label_format, template, count))
        thread.start()
        self.progress_dialog.exec_()
        thread.join()
        self.__printing = False

    @QtCore.pyqtSlot()
    def __onLineFilter_textChanged(self):
        new_string = self.ui.lineFilter.text().lower()
        for i in range(self.ui.listProducts.count()):
            item = self.ui.listProducts.item(i)
            if new_string in item.text().lower():
                item.setHidden(False)
            else:
                item.setHidden(True)

    def __setup_update_ui(self, check_updates):
        self.__update_button = QtWidgets.QPushButton("Обновить")
        self.__update_button.setEnabled(False)
        self.__update_button.clicked.connect(self.__onUpdateButtonClicked)
        self.statusBar().addWidget(self.__update_button)
        if not check_updates:
            return
        self.__update_service = UpdateService(self)
        self.__update_service.update_available.connect(self.__onUpdateAvailable)
        self.__update_service.progress_changed.connect(self.__change_progress)
        self.__update_service.finished.connect(self.__onUpdateFinished)
        self.__update_service.start_check()

    @QtCore.pyqtSlot(str)
    def __onUpdateAvailable(self, tag):
        self.statusBar().showMessage("Доступна новая версия {}".format(tag), 10000)
        self.__update_button.setEnabled(True)

    @QtCore.pyqtSlot()
    def __onUpdateButtonClicked(self):
        if self.__printing:
            QtWidgets.QMessageBox.warning(self, "Обновление", "Нельзя обновляться во время печати")
            return
        self.progress_dialog = QProgressDialog("Обновление...", None, 0, 3)
        self.progress_dialog.setAutoClose(True)
        self.__update_service.update()
        self.progress_dialog.exec_()

    @QtCore.pyqtSlot(bool, str)
    def __onUpdateFinished(self, success, message):
        if self.progress_dialog is not None:
            self.progress_dialog.close()
        if not success:
            self.error_expected.emit(message)
            return
        QtCore.QProcess.startDetached(sys.executable, ["-m", "PrintLabelMS"])
        self.close()
