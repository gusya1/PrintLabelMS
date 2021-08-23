from PyQt5 import QtWidgets, QtCore
import sys
from MainWindow import MainWindow, LabelFormat, PrintLabelException
from MSApi.MSApi import MSApi, MSApiException
import asyncio


def fatal_error(message):
    QtWidgets.QMessageBox.critical(None, "Error", str(message))
    app.exit(1)
    exit()


async def show_progress():
    progress_dialog = QtWidgets.QProgressDialog("Initialized", None, 0, 3, None)
    progress_dialog.setAutoClose(True)
    progress_dialog.exec()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    try:
        if len(app.arguments()) != 2:
            fatal_error("Invalid arguments.\nUsage: python3 MapGenerator <settings_file>")

        # asyncio.run(show_progress())

        config_path = app.arguments()[1]

        window = MainWindow(config_path)
        # MainWindow.set_print_resolution(int(config['printer']['resolution']))


        window.show()
        app.exec()

    except PrintLabelException as e:
        fatal_error(e)
    except MSApiException as e:
        fatal_error(e)




