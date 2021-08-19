from PyQt5 import uic, QtWidgets, QtCore
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import QSizeF, QByteArray
from PyQt5.QtGui import QPainter, QPixmap, QPageLayout
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
# from PyQt5.QtCore import QMarginsF

from moysklad.api import MoySklad
# from moysklad.queries import Expand, Filter, Ordering, Select, Search, Query
import io
import requests
import pdf2image
import pdf2image.exceptions


class PrintLabelException(Exception): pass


class LabelSize(object):

    @classmethod
    def from_str(cls, string: str):
        size_str_list = string.split('x')
        return LabelSize(int(size_str_list[0]), int(size_str_list[1]))

    def __init__(self, width=0, height=0):
        self.width = width
        self.height = height

    def __str__(self):
        return f"{self.width}x{self.height}"


class MainWindow(QMainWindow):
    __sklad: MoySklad = None
    __token = None
    __printer = None
    __sizes = []

    def __error(self, err):
        QtWidgets.QMessageBox.critical(self, "Error", str(err))

    @classmethod
    def moy_sklad_login(cls, login: str, password: str):
        import base64
        cls.__sklad = MoySklad.get_instance(login, password)
        auch_base64 = base64.b64encode(f"{login}:{password}".encode('utf-8')).decode('utf-8')
        response = requests.post(f"{cls.__sklad.get_client().endpoint}/security/token",
                                 headers={"Authorization": f"Basic {auch_base64}"})
        if response.status_code != 201:
            raise PrintLabelException(response.json().get('errors')[0].get('error'))
        cls.__token = str(response.json()["access_token"])
        cls.__sklad.set_pos_token(cls.__token)

    @classmethod
    def set_printer_name(cls, printer_name: str):
        cls.__printer = QPrinter()
        cls.__printer.setPrinterName(printer_name)
        if not cls.__printer.isValid():
            raise PrintLabelException(f"Printer \"{printer_name}\" not found")

    @classmethod
    def set_print_resolution(cls, resolution: int):
        cls.__printer.setResolution(600)

    @classmethod
    def set_label_sizes(cls, sizes: [LabelSize]):
        cls.__sizes = sizes

    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi("mainwindow.ui", self)

        client = self.__sklad.get_client()
        methods = self.__sklad.get_methods()

        self.btnPrint.clicked.connect(self.onBtnPrint_clicked)
        self.lineFilter.textChanged.connect(self.onLineFilter_textChanged)

        for size in self.__sizes:
            self.comboLabelSize.addItem(str(size), size)

        product_response = client.get(method=methods.get_list_url('product'))
        for row in product_response.rows:
            self.listProducts.addItem(row.get('name'))
        self.__products = product_response.rows

        template_response = client.get(method=methods.get_list_url('assortment/metadata/customtemplate'))
        for row in template_response.rows:
            self.comboLabelFormat.addItem(row.get('name'), row)

        organization_response = client.get(method=methods.get_list_url('organization'))
        if len(organization_response.rows) == 0:
            raise PrintLabelException("Could not find organization")
        self.__organization = organization_response.rows[0]

    @QtCore.pyqtSlot()
    def onBtnPrint_clicked(self):
        try:
            if self.__printer is None:
                raise PrintLabelException("Printer not initialised")

            product_items = self.listProducts.selectedItems()
            if len(product_items) == 0:
                raise PrintLabelException("Product not selected")

            product = self.__products[self.listProducts.row(product_items[0])]

            sale_prices = product.get('salePrices')
            if len(sale_prices) == 0:
                raise PrintLabelException(f"Sale price not found in {product}")

            request_json = {
                'organization': {
                    'meta': self.__organization.get('meta')
                },
                'count': 1,
                'salePrice': sale_prices[0],
                'template': self.comboLabelFormat.currentData()
            }

            response = requests.post(f"{self.__sklad.get_client().endpoint}entity/product/{product.get('id')}/export",
                                     headers={"Authorization": f"Bearer {self.__token}",
                                              "Content-Type": "application/json"},
                                     json=request_json)

            if response.status_code == 303:
                url = response.json().get('Location')
                file_response = requests.get(url)
                data = file_response.content
            elif response.status_code == 200:
                data = response.content
            else:
                raise PrintLabelException(response.json().get('errors')[0].get('error'))

            pages = pdf2image.convert_from_bytes(data, self.__printer.resolution())
            pages[0].save('data/out.jpg', 'JPEG')
            img_bytes = io.BytesIO()
            pages[0].save(img_bytes, format='JPEG')
            img_bytes = img_bytes.getvalue()

            size = self.comboLabelSize.currentData()
            self.__printer.setPageSizeMM(QSizeF(size.width, size.height))
            if self.checkRotate90.isChecked():
                self.__printer.setPageOrientation(QPageLayout.Orientation.Landscape)
            else:
                self.__printer.setPageOrientation(QPageLayout.Orientation.Portrait)

            self.__printer.setCopyCount(self.spinCount.value())

            pixmap = QPixmap()
            pixmap.loadFromData(QByteArray(img_bytes), format='JPEG')

            painter = QPainter()
            painter.begin(self.__printer)
            painter.drawPixmap(0, 0, pixmap)
            painter.end()

        except pdf2image.exceptions.PDFInfoNotInstalledError as e:
            self.__error(e)
        except PrintLabelException as e:
            self.__error(e)

    @QtCore.pyqtSlot()
    def onLineFilter_textChanged(self):
        new_string = self.lineFilter.text().lower()
        for i in range(self.listProducts.count()):
            item = self.listProducts.item(i)
            if new_string in item.text().lower():
                item.setHidden(False)
            else:
                item.setHidden(True)


