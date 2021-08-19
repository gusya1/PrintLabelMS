from PyQt5 import QtWidgets
import sys
import configparser
from mainwindow import MainWindow, LabelSize, PrintLabelException

def fatal_error(message):
    QtWidgets.QMessageBox.critical(None, "Error", str(message))
    app.exit(1)
    exit()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    try:
        if len(app.arguments()) != 2:
            fatal_error("Invalid arguments.\nUsage: python3 MapGenerator <settings_file>")

        config_path = app.arguments()[1]

        config = configparser.ConfigParser()
        config.read(config_path, encoding="utf-8")

        MainWindow.moy_sklad_login(config['moy_sklad']['login'],
                                   config['moy_sklad']['password'])

        MainWindow.set_printer_name(config['printer']['name'])
        MainWindow.set_print_resolution(int(config['printer']['resolution']))

        sizes = []
        for size_str in config['printer']['sizes'].split('\n'):
            if not size_str:
                continue
            sizes.append(LabelSize.from_str(size_str))
        MainWindow.set_label_sizes(sizes)

        window = MainWindow()
        window.show()
        app.exec()

    except PrintLabelException as e:
        fatal_error(e)




