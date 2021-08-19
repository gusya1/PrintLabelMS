from PyQt5 import QtWidgets
import sys
import configparser
from mainwindow import MainWindow

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    config = configparser.ConfigParser()
    config.read("settings.ini", encoding="utf-8")

    MainWindow.moy_sklad_login(config['moy_sklad']['login'],
                               config['moy_sklad']['password'])
    window = MainWindow()
    window.show()
    app.exec()


