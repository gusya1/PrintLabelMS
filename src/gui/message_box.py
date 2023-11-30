from PyQt5 import QtWidgets


def fatal_error(message):
    QtWidgets.QMessageBox.critical(None, "Ошибка", str(message))