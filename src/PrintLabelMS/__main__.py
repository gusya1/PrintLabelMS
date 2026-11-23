import argparse
import importlib.metadata
import sys
from pathlib import Path

import updater
from updater.paths import APP_NAME, config_path


def _app_version():
    try:
        return importlib.metadata.version(APP_NAME)
    except importlib.metadata.PackageNotFoundError:
        return "unknown"


def _default_settings_path():
    return config_path()


def _print_version():
    print("{} {}".format(APP_NAME, _app_version()))
    print("Python {}".format(sys.version.split()[0]))
    for package in ("PyQt5", "pydantic", "pypdfium2"):
        try:
            version = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            version = "unknown"
        print("{} {}".format(package, version))
    return 0


def _cmd_update(args):
    try:
        return updater.update(target_version=args.target_version, check_only=args.check)
    except updater.UpdaterError as e:
        print(str(e), file=sys.stderr)
        return 1


def _cmd_rollback(args):
    try:
        return updater.rollback()
    except updater.UpdaterError as e:
        print(str(e), file=sys.stderr)
        return 1


def _run_gui(settings_path):
    from PyQt5 import QtWidgets
    from pydantic import ValidationError

    import gui.message_box
    import gui.splash_screen
    from config import read_config
    from gui.MainWindow import MainWindow
    from moysklad_manager.exceptions import MoySkladError
    from moysklad_manager.manager import MoySkladManager
    from PrintLabelMS.print_handler import PrintHandler
    from pdf_to_image_converter.converter import Converter

    app = QtWidgets.QApplication(sys.argv)
    splash = gui.splash_screen.get_splash_screen()
    splash.show()

    def fatal_error(message):
        gui.message_box.fatal_error(str(message))
        app.exit(1)
        sys.exit(1)

    try:
        config_model = read_config(settings_path)
        manager = MoySkladManager(config_model.moy_sklad_token)
        converter = Converter()
        print_handler = PrintHandler(config_model.printer.name, config_model.printer.resolution, converter)
        assortment = manager.get_assortment()
        templates = manager.get_custom_templates()
        organizations = manager.get_organizations()
        if not organizations:
            raise RuntimeError("Организация не найдена")
        organization = organizations[0]
        window = MainWindow(print_handler, manager, config_model.label_formats, assortment, templates, organization,
                            check_updates=config_model.check_updates)
        window.show()
        splash.finish(window)
        return app.exec()
    except (MoySkladError, ValidationError, OSError, RuntimeError) as e:
        fatal_error(e)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in ("update", "rollback"):
        command = argv.pop(0)
        parser = argparse.ArgumentParser(prog="{} {}".format(APP_NAME, command))
        if command == "update":
            parser.add_argument("--to", dest="target_version", default=None, metavar="X.Y.Z")
            parser.add_argument("--check", action="store_true")
            args = parser.parse_args(argv)
            return _cmd_update(args)
        args = parser.parse_args(argv)
        return _cmd_rollback(args)
    parser = argparse.ArgumentParser(prog=APP_NAME)
    parser.add_argument("settings", nargs="?", default=None,
                        help="Путь к settings.json (по умолчанию ~/.config/{}/settings.json)".format(APP_NAME))
    parser.add_argument("--version", action="store_true", help="Версии приложения и зависимостей")
    args = parser.parse_args(argv)
    if args.version:
        return _print_version()
    settings_path = Path(args.settings) if args.settings else _default_settings_path()
    return _run_gui(settings_path)


if __name__ == "__main__":
    sys.exit(main())
