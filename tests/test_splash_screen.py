import os

import pytest
from PyQt5 import QtWidgets


@pytest.fixture(scope="module")
def qapp():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def test_splash_pixmap_has_no_alpha(qapp):
    from gui.splash_screen import get_splash_screen

    splash = get_splash_screen()
    image = splash.pixmap().toImage()
    assert not image.hasAlphaChannel()


def test_splash_corners_are_white(qapp):
    from gui.splash_screen import get_splash_screen

    splash = get_splash_screen()
    image = splash.pixmap().toImage()
    width, height = image.width(), image.height()
    for x, y in ((0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1)):
        color = image.pixelColor(x, y)
        assert (color.red(), color.green(), color.blue()) == (255, 255, 255)


def test_splash_message(qapp):
    from gui.splash_screen import get_splash_screen

    splash = get_splash_screen()
    assert splash.message() == "Загружаем товары..."
