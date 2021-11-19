from PyQt5 import QtWidgets, QtGui
import sys
from MainWindow import MainWindow, PrintLabelException
from MSApi import MSApiException


def fatal_error(message):
    QtWidgets.QMessageBox.critical(None, "Error", str(message))
    app.exit(1)
    exit()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    try:
        if len(app.arguments()) != 2:
            fatal_error("Invalid arguments.\nUsage: python3 MapGenerator <settings_file>")

        splash = QtWidgets.QSplashScreen(QtGui.QPixmap("pictures/snm_logo.png"))
        splash.showMessage("Initialisation...")
        splash.show()

        config_path = app.arguments()[1]

        window = MainWindow(config_path)
        window.show()
        splash.finish(window)
        app.exec()

    except PrintLabelException as e:
        fatal_error(e)
    except MSApiException as e:
        fatal_error(e)




