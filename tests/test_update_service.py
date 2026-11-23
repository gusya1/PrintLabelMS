import os
import time

import pytest
from PyQt5 import QtCore

import updater
from gui.update_service import UpdateService


@pytest.fixture
def qapp():
    return QtCore.QCoreApplication.instance() or QtCore.QCoreApplication([])


@pytest.fixture
def env(tmp_path, monkeypatch):
    paths = {
        "data": tmp_path / "data",
        "config": tmp_path / "config",
        "state": tmp_path / "state",
        "cache": tmp_path / "cache",
    }
    monkeypatch.setenv("XDG_DATA_HOME", str(paths["data"]))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(paths["config"]))
    monkeypatch.setenv("XDG_STATE_HOME", str(paths["state"]))
    monkeypatch.setenv("XDG_CACHE_HOME", str(paths["cache"]))
    return paths


def _install(env, version):
    data = env["data"] / "printlabelms"
    version_dir = data / "versions" / version
    version_dir.mkdir(parents=True)
    os.symlink(version_dir, data / "current")


def _wait_for(qapp, predicate, timeout=5.0):
    deadline = time.time() + timeout
    while not predicate():
        qapp.processEvents()
        if time.time() >= deadline:
            return False
        time.sleep(0.01)
    return True


def test_start_check_not_installed(env, monkeypatch):
    calls = []
    monkeypatch.setattr("updater.release.fetch_latest_release", lambda: calls.append(1))
    service = UpdateService()
    assert not service.installed
    service.start_check()
    time.sleep(0.2)
    assert calls == []


def test_check_emits_newer_version(qapp, env, monkeypatch):
    _install(env, "0.1.0")
    monkeypatch.setattr("updater.release.fetch_latest_release", lambda: {"tag_name": "v0.2.0"})
    service = UpdateService()
    tags = []
    service.update_available.connect(lambda tag: tags.append(tag))
    service.start_check()
    assert _wait_for(qapp, lambda: len(tags) == 1)
    assert tags[0] == "v0.2.0"


def test_check_no_emit_when_not_newer(qapp, env, monkeypatch):
    _install(env, "0.2.0")
    monkeypatch.setattr("updater.release.fetch_latest_release", lambda: {"tag_name": "v0.2.0"})
    service = UpdateService()
    tags = []
    service.update_available.connect(lambda tag: tags.append(tag))
    service.start_check()
    time.sleep(0.3)
    assert tags == []


def test_check_invalid_tag_silent(qapp, env, monkeypatch):
    _install(env, "0.1.0")
    monkeypatch.setattr("updater.release.fetch_latest_release", lambda: {"tag_name": "not-a-version"})
    service = UpdateService()
    tags = []
    service.update_available.connect(lambda tag: tags.append(tag))
    service.start_check()
    time.sleep(0.3)
    assert tags == []


def test_update_success(qapp, env, monkeypatch):
    _install(env, "0.2.0")
    called = {}

    def fake_update(target_version=None):
        called["target"] = target_version

    monkeypatch.setattr("updater.update", fake_update)
    service = UpdateService()
    results = []
    progress = []
    service.finished.connect(lambda ok, msg: results.append((ok, msg)))
    service.progress_changed.connect(lambda message, value: progress.append((message, value)))
    service.update(target_version="0.3.0")
    assert _wait_for(qapp, lambda: len(results) == 1)
    assert results[0] == (True, "")
    assert called["target"] == "0.3.0"
    assert ("Обновление завершено", 3) in progress


def test_update_failure(qapp, env, monkeypatch):
    _install(env, "0.2.0")

    def fake_update(target_version=None):
        raise updater.UpdaterError("сбой обновления")

    monkeypatch.setattr("updater.update", fake_update)
    service = UpdateService()
    results = []
    service.finished.connect(lambda ok, msg: results.append((ok, msg)))
    service.update()
    assert _wait_for(qapp, lambda: len(results) == 1)
    assert results[0] == (False, "сбой обновления")


def test_rollback_success(qapp, env, monkeypatch):
    _install(env, "0.2.0")
    monkeypatch.setattr("updater.rollback", lambda: None)
    service = UpdateService()
    results = []
    service.finished.connect(lambda ok, msg: results.append((ok, msg)))
    service.rollback()
    assert _wait_for(qapp, lambda: len(results) == 1)
    assert results[0] == (True, "")


def test_rollback_failure(qapp, env, monkeypatch):
    _install(env, "0.2.0")

    def fake_rollback():
        raise updater.UpdaterError("сбой отката")

    monkeypatch.setattr("updater.rollback", fake_rollback)
    service = UpdateService()
    results = []
    service.finished.connect(lambda ok, msg: results.append((ok, msg)))
    service.rollback()
    assert _wait_for(qapp, lambda: len(results) == 1)
    assert results[0] == (False, "сбой отката")


def test_current_version_from_symlink(env):
    _install(env, "0.3.2")
    service = UpdateService()
    assert service.current_version() == "v0.3.2"


def test_current_version_fallback_to_package_metadata(env, monkeypatch):
    monkeypatch.setattr("importlib.metadata.version", lambda name: "9.9.9")
    service = UpdateService()
    assert service.current_version() == "v9.9.9"
