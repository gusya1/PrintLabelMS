from PyQt5 import QtWidgets, QtGui

import resources


def get_splash_screen():
    splash = QtWidgets.QSplashScreen(QtGui.QPixmap(resources.get_resource_path("pictures/snm_logo.png")))
    splash.showMessage("Initialisation...")
    return splash
