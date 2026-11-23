import os
import sys
import types
import weakref
from types import SimpleNamespace

import pytest
from PyQt5 import QtCore, QtWidgets


@pytest.fixture(scope="module")
def qapp():
    # QApplication здесь не создаём: _run_gui обязан запуститься как при
    # реальном старте — с единственным экземпляром приложения. Второй
    # экземпляр, уничтожаемый рядом с живым, роняет процесс при завершении.
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    return QtWidgets.QApplication.instance()


class FakeLoader(QtCore.QObject):

    """Заглушка StartupLoader: start() сразу эмитит loaded (кадр слота умирает после возврата из emit)."""

    loaded = QtCore.pyqtSignal(object)
    error = QtCore.pyqtSignal(str)

    def __init__(self, settings_path, bundle):
        super().__init__()
        self.__bundle = bundle

    def start(self):
        self.loaded.emit(self.__bundle)


class FakeMainWindow(QtWidgets.QWidget):

    """Заглушка MainWindow: принимает аргументы реального конструктора, записывает weakref на себя."""

    refs = []

    def __init__(self, print_handler, manager, label_formats, assortment, templates, organization,
                 check_updates=True, parent=None):
        super().__init__(parent)
        FakeMainWindow.refs.append(weakref.ref(self))


def _bundle():
    config_model = SimpleNamespace(
        ui_scale=1.0,
        printer=SimpleNamespace(name="printer", resolution=300),
        label_formats=[],
        check_updates=False,
    )
    return (config_model, object(), [], [], object())


def test_window_survives_slot_return(qapp, monkeypatch):
    from PrintLabelMS.__main__ import _run_gui

    FakeMainWindow.refs = []
    bundle = _bundle()
    # Модуль gui.MainWindow подменяется целиком: в CI папка gui/ui/ не
    # генерирована, и реальный импорт модуля невозможен.
    fake_mainwindow_module = types.ModuleType("gui.MainWindow")
    fake_mainwindow_module.MainWindow = FakeMainWindow
    monkeypatch.setitem(sys.modules, "gui.MainWindow", fake_mainwindow_module)
    monkeypatch.setattr("PrintLabelMS.startup_loader.StartupLoader", lambda path: FakeLoader(path, bundle))
    monkeypatch.setattr("PrintLabelMS.print_handler.PrintHandler", lambda *args: object())
    monkeypatch.setattr("pdf_to_image_converter.converter.Converter", lambda: object())
    fatal_calls = []
    monkeypatch.setattr("gui.message_box.fatal_error", lambda message: fatal_calls.append(message))

    alive_at_exec = {}

    def fake_exec(self):
        for _ in range(3):
            self.processEvents()
        alive_at_exec["window"] = FakeMainWindow.refs[0]() if FakeMainWindow.refs else None
        return 0

    monkeypatch.setattr(QtWidgets.QApplication, "exec", fake_exec)
    assert _run_gui("/nonexistent/settings.json") == 0
    assert fatal_calls == []
    assert len(FakeMainWindow.refs) == 1
    # Окно, созданное по сигналу загрузчика, живо во время app.exec():
    # без удержания владельцем PyQt удаляет его после возврата из слота.
    assert alive_at_exec["window"] is not None
