from PyQt5 import QtWidgets, QtCore
import sys
import configparser
from MainWindow import MainWindow, LabelFormat, PrintLabelException
from MSApi.MSApi import MSApi, MSApiException


def fatal_error(message):
    QtWidgets.QMessageBox.critical(None, "Error", str(message))
    app.exit(1)
    exit()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    try:
        if len(app.arguments()) != 2:
            fatal_error("Invalid arguments.\nUsage: python3 MapGenerator <settings_file>")

        progress_dialog = QtWidgets.QProgressDialog("Initialized", "None", 0, 3, None)
        progress_dialog.setAutoClose(True)
        # progress_dialog.setWindowModality(QtCore.Qt.WindowModality.WindowModal)


        config_path = app.arguments()[1]

        config = configparser.ConfigParser()
        config.read(config_path, encoding="utf-8")

        MSApi.login(config['moy_sklad']['login'], config['moy_sklad']['password'])

        sizes = []
        for size_str in config['printer']['sizes'].split('\n'):
            if not size_str:
                continue
            sizes.append(LabelFormat.from_str(size_str))

        window = MainWindow()
        window.set_printer(config['printer']['name'])
        window.set_label_formats(sizes)
        # MainWindow.set_print_resolution(int(config['printer']['resolution']))


        window.show()
        app.exec()

    except PrintLabelException as e:
        fatal_error(e)
    except MSApiException as e:
        fatal_error(e)




