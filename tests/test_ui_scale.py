import os

import pytest
from PyQt5 import QtWidgets, QtGui

from gui.ui_scale import apply_ui_scale


@pytest.fixture(scope="module")
def qapp():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


@pytest.fixture
def restore_font(qapp):
    original = QtGui.QFont(qapp.font())
    yield
    qapp.setFont(original)


def test_ui_scale_one_is_noop(qapp, restore_font):
    base_point_size = qapp.font().pointSizeF()
    apply_ui_scale(qapp, 1.0)
    assert qapp.font().pointSizeF() == base_point_size


def test_ui_scale_two_doubles_point_size(qapp, restore_font):
    base_point_size = qapp.font().pointSizeF()
    apply_ui_scale(qapp, 2.0)
    assert qapp.font().pointSizeF() == pytest.approx(base_point_size * 2.0)


def test_ui_scale_half_halves_point_size(qapp, restore_font):
    base_point_size = qapp.font().pointSizeF()
    apply_ui_scale(qapp, 0.5)
    assert qapp.font().pointSizeF() == pytest.approx(base_point_size * 0.5)
