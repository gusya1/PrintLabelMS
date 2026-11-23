import os

import pytest
from PyQt5 import QtCore, QtGui, QtWidgets

from PrintLabelMS.print_handler import CALIBRATION_LINE_WIDTH_MM, draw_calibration, mm_to_device_pixels


@pytest.fixture(scope="module")
def qapp():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def test_mm_to_device_pixels_at_600dpi():
    assert mm_to_device_pixels(10, 600) == 236
    assert mm_to_device_pixels(-1, 600) == -24
    assert mm_to_device_pixels(0, 600) == 0


def test_mm_to_device_pixels_at_300dpi():
    assert mm_to_device_pixels(10, 300) == 118
    assert mm_to_device_pixels(-5, 300) == -59


def test_calibration_line_width_is_positive():
    assert CALIBRATION_LINE_WIDTH_MM > 0


def test_draw_calibration_draws_frame_and_diagonals(qapp):
    image = QtGui.QImage(100, 60, QtGui.QImage.Format_RGB32)
    image.fill(QtCore.Qt.white)

    painter = QtGui.QPainter(image)
    draw_calibration(painter, 100, 60, 2)
    painter.end()

    def is_dark(x, y):
        return image.pixelColor(x, y).lightness() < 128

    assert is_dark(50, 1)
    assert is_dark(50, 58)
    assert is_dark(1, 30)
    assert is_dark(98, 30)
    assert is_dark(50, 30)
    assert not is_dark(80, 30)
