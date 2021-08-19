from PyQt5 import uic, QtWidgets, QtCore
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import QSizeF
from PyQt5.QtGui import QPainter, QPixmap, QPageLayout
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
# from PyQt5.QtCore import QMarginsF

from moysklad.api import MoySklad
# from moysklad.queries import Expand, Filter, Ordering, Select, Search, Query
import json
import requests
import pdf2image
import pdf2image.exceptions


class MainWindow(QMainWindow):

    __sklad: MoySklad = None
    __token = None

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
            raise Exception(response.json().get('errors')[0].get('error'))  # TODO error
        cls.__token = str(response.json()["access_token"])
        cls.__sklad.set_pos_token(cls.__token)

    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi("mainwindow.ui", self)

        client = self.__sklad.get_client()
        methods = self.__sklad.get_methods()

        # self.btnPrint.clicked.connect(self.on_btnPrint_clicked)

        product_response = client.get(method=methods.get_list_url('product'))
        for row in product_response.rows:
            self.listProducts.addItem(row.get('name'))
        self.__products = product_response.rows

        template_response = client.get(method=methods.get_list_url('assortment/metadata/customtemplate'))
        for row in template_response.rows:
            self.comboLabelFormat.addItem(row.get('name'))
        self.__templates = template_response.rows

        organization_response = client.get(method=methods.get_list_url('organization'))
        if len(organization_response.rows) == 0:
            self.__error("Could not find organization")
            return  # TODO exception
        self.__organization = organization_response.rows[0]

    @QtCore.pyqtSlot()
    def on_btnPrint_clicked(self):
        try:
            product_items = self.listProducts.selectedItems()
            if len(product_items) == 0:
                raise Exception("")  # TODO error

            product = self.__products[self.listProducts.row(product_items[0])]

            sale_prices = product.get('salePrices')
            if len(sale_prices) == 0:
                raise Exception("")  # TODO error

            request_json = {
                'organization': {
                    'meta': self.__organization.get('meta')
                },
                'count': 1,
                'salePrice': sale_prices[0],
                'template': self.__templates[0]  # FIXME set combo
            }

            json.dumps(request_json)

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
                raise Exception(response.json().get('errors')[0].get('error'))  # TODO error

            file = open("data/label.pdf", 'wb')
            file.write(data)
            file.close()

            pages = pdf2image.convert_from_path('data/label.pdf', 600)
            pages[0].save('data/out.jpg', 'JPEG')

            printer = QPrinter()
            printer.setPrinterName("TSC TE200")
            if not printer.isValid():
                raise Exception("Printer is not Valid")  # TODO error

            printer.setResolution(600)
            printer.setPageSizeMM(QSizeF(58, 39))
            printer.setPageOrientation(QPageLayout.Orientation.Portrait)
            printer.setCopyCount(1)

            pixmap = QPixmap('data/out.jpg')

            painter = QPainter()

            painter.begin(printer)
            painter.drawPixmap(0, 0, pixmap)
            painter.end()

        except pdf2image.exceptions.PDFInfoNotInstalledError as e:
            self.__error(e)
