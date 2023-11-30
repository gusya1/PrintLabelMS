import os
import subprocess
import logging


class BuildError(Exception):
    pass


def get_build_directory():
    return os.path.dirname(os.path.abspath(__file__))


def filter_current_directory_files(extension):
    build_directory = get_build_directory()
    return list(os.path.join(build_directory, filename) for filename in os.listdir(build_directory) if
                filename.endswith(".{}".format(extension)))


UI_DIR = "ui"

UI_FORM_LIST = filter_current_directory_files('ui')


def generate_ui():
    build_dir = get_build_directory()
    for form_path in UI_FORM_LIST:
        ui_path, ui_filename = os.path.split(form_path)
        ui_filename_base, _ = os.path.splitext(ui_filename)
        result = subprocess.run(
            ["pyuic5", "-o", os.path.join(build_dir, UI_DIR, "{}_ui.py".format(ui_filename_base)), form_path])
        if result.returncode != 0:
            raise BuildError("\"{}\" form build failed: {}".format(form_path, result.stderr))
        logging.info("Build form completed")


def generate_ui():
    import PyQt5.uic
    ui_compiler = PyQt5.uic.compiler.UICompiler()

    build_dir = get_build_directory()

    for form_path in UI_FORM_LIST:
        try:
            ui_path, ui_filename = os.path.split(form_path)
            ui_filename_base, _ = os.path.splitext(ui_filename)

            output_file_name = "{}_ui.py".format(ui_filename_base)
            output_file_path = os.path.join(build_dir, UI_DIR, output_file_name)
            output_file = open(output_file_path, "w", encoding="utf-8")

            ui_compiler.reset()
            ui_compiler.resources = []
            ui_compiler.compileUi(os.path.abspath(form_path),
                                  output_file,
                                  False, "", None)
            output_file.close()

        except SyntaxError as e:
            raise BuildError("\"{}\" form parse failed: {}".format(form_path, str(e)))


if __name__ == "__main__":
    try:
        generate_ui()
    except BuildError as e:
        logging.error(str(e))
