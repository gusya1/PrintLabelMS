from PyQt5 import QtWidgets, QtGui

import resources


def get_splash_screen():
    logo = QtGui.QPixmap(resources.get_resource_path("pictures/snm_logo.png"))
    image = QtGui.QImage(logo.size(), QtGui.QImage.Format_RGB32)
    image.fill(QtGui.QColor("white"))
    painter = QtGui.QPainter(image)
    painter.drawImage(0, 0, logo.toImage())
    painter.end()
    splash = QtWidgets.QSplashScreen(QtGui.QPixmap.fromImage(image))
    splash.showMessage("Загружаем товары...")
    return splash
