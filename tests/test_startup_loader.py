import time

import pytest
from PyQt5 import QtCore

from PrintLabelMS.startup_loader import StartupLoader
from config import Config, LabelFormat, Orientation, PrinterConfig


@pytest.fixture
def qapp():
    return QtCore.QCoreApplication.instance() or QtCore.QCoreApplication([])


def _wait_for(qapp, predicate, timeout=5.0):
    deadline = time.time() + timeout
    while not predicate():
        qapp.processEvents()
        if time.time() >= deadline:
            return False
        time.sleep(0.01)
    return True


def _config():
    return Config(
        moy_sklad_token="token",
        printer=PrinterConfig(name="printer", resolution=300),
        label_formats=[LabelFormat(width=58, height=40, width_offset=0, height_offset=0,
                                   orientation=Orientation.PORTRAIT)],
    )


class FakeManager:

    def __init__(self, token):
        self.token = token
        self.assortment = ["товар 1", "товар 2"]
        self.templates = ["шаблон 1"]
        self.organizations = ["организация 1", "организация 2"]

    def get_assortment(self):
        return self.assortment

    def get_custom_templates(self):
        return self.templates

    def get_organizations(self):
        return self.organizations


def test_loaded_emits_bundle(qapp, monkeypatch):
    monkeypatch.setattr("PrintLabelMS.startup_loader.read_config", lambda path: _config())
    monkeypatch.setattr("PrintLabelMS.startup_loader.MoySkladManager", FakeManager)
    loader = StartupLoader("/nonexistent/settings.json")
    bundles = []
    errors = []
    loader.loaded.connect(lambda bundle: bundles.append(bundle))
    loader.error.connect(lambda message: errors.append(message))
    loader.start()
    assert _wait_for(qapp, lambda: len(bundles) == 1)
    config_model, manager, assortment, templates, organization = bundles[0]
    assert isinstance(config_model, Config)
    assert isinstance(manager, FakeManager)
    assert manager.token == "token"
    assert assortment == ["товар 1", "товар 2"]
    assert templates == ["шаблон 1"]
    assert organization == "организация 1"
    assert errors == []


def test_no_organizations_emits_error(qapp, monkeypatch):
    monkeypatch.setattr("PrintLabelMS.startup_loader.read_config", lambda path: _config())

    class NoOrgManager(FakeManager):
        def get_organizations(self):
            return []

    monkeypatch.setattr("PrintLabelMS.startup_loader.MoySkladManager", NoOrgManager)
    loader = StartupLoader("/nonexistent/settings.json")
    bundles = []
    errors = []
    loader.loaded.connect(lambda bundle: bundles.append(bundle))
    loader.error.connect(lambda message: errors.append(message))
    loader.start()
    assert _wait_for(qapp, lambda: len(errors) == 1)
    assert errors[0] == "Организация не найдена"
    assert bundles == []


def test_read_config_error_emits_error(qapp, monkeypatch):
    def fake_read_config(path):
        raise ValueError("сбой конфига")

    monkeypatch.setattr("PrintLabelMS.startup_loader.read_config", fake_read_config)
    loader = StartupLoader("/nonexistent/settings.json")
    bundles = []
    errors = []
    loader.loaded.connect(lambda bundle: bundles.append(bundle))
    loader.error.connect(lambda message: errors.append(message))
    loader.start()
    assert _wait_for(qapp, lambda: len(errors) == 1)
    assert errors[0] == "сбой конфига"
    assert bundles == []


def test_assortment_error_emits_error(qapp, monkeypatch):
    monkeypatch.setattr("PrintLabelMS.startup_loader.read_config", lambda path: _config())

    class FailingManager(FakeManager):
        def get_assortment(self):
            raise RuntimeError("сбой сети")

    monkeypatch.setattr("PrintLabelMS.startup_loader.MoySkladManager", FailingManager)
    loader = StartupLoader("/nonexistent/settings.json")
    bundles = []
    errors = []
    loader.loaded.connect(lambda bundle: bundles.append(bundle))
    loader.error.connect(lambda message: errors.append(message))
    loader.start()
    assert _wait_for(qapp, lambda: len(errors) == 1)
    assert errors[0] == "сбой сети"
    assert bundles == []
