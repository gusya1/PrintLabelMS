import requests
from PyQt5 import QtWidgets

import sys

from MSApi import MSApiException
from MSApi import MSApi
from pydantic import ValidationError

import gui.splash_screen
import gui.message_box
from gui.MainWindow import MainWindow
import config
import moy_sklad
from PrintLabelMS.print_handler import PrintHandler
from pdf_to_image_converter.converter import Converter


def fatal_error(message):
    gui.message_box.fatal_error(message)
    app.exit(1)
    exit()


if __name__ == '__main__':
    try:
        app = QtWidgets.QApplication(sys.argv)

        if len(app.arguments()) != 2:
            print("Invalid arguments.\nUsage: python src/PrintLabelMS/__main__.py <setting_file>")
            exit(1)

        splash = gui.splash_screen.get_splash_screen()
        splash.show()

        config_path = app.arguments()[1]
        config_model = config.read_config(config_path)

        MSApi.set_access_token(config_model.moy_sklad_token)

        converter = Converter(config_model.poppler_path)
        print_handler = PrintHandler(config_model.printer.name, config_model.printer.resolution, converter)

        assortment = moy_sklad.get_assortment()
        templates = moy_sklad.get_assortment_custom_templates()

        organizations = moy_sklad.get_organizations()
        if not organizations:
            raise RuntimeError("Организация не найдена")
        organization = organizations[0]

        window = MainWindow(print_handler, config_model.label_formats, assortment, templates, organization)
        window.show()

        splash.finish(window)
        app.exec()
    except MSApiException as e:
        fatal_error(e)
    except requests.exceptions.RequestException as e:
        fatal_error(e)
    except ValidationError as e:
        fatal_error(e)
    except OSError as e:
        fatal_error(e)
    except RuntimeError as e:
        fatal_error(e)
