import hashlib
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

import updater
from updater import installer, release

WHEEL_NAME = "printlabelms-0.3.0-py3-none-any.whl"
WHEEL_BYTES = b"wheel-bytes"
WHEEL_SHA = hashlib.sha256(WHEEL_BYTES).hexdigest()


def _result(returncode=0, stdout="", stderr=""):
    return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)


def _link_target(link):
    target = os.readlink(str(link))
    if target.startswith("\\\\?\\"):
        target = target[4:]
    return Path(target)


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


@pytest.fixture
def installed(env):
    data = env["data"] / "printlabelms"
    version_dir = data / "versions" / "0.2.0"
    bin_dir = version_dir / "venv" / "bin"
    bin_dir.mkdir(parents=True)
    (bin_dir / "printlabelms").touch()
    (bin_dir / "python").touch()
    os.symlink(version_dir, data / "current")
    config_file = env["config"] / "printlabelms" / "settings.json"
    config_file.parent.mkdir(parents=True)
    config_file.write_text('{"schema_version": 2}', encoding="utf-8")


@pytest.fixture
def fake_release(monkeypatch):
    assets = [
        {"name": WHEEL_NAME, "browser_download_url": "https://example.com/{}".format(WHEEL_NAME)},
        {"name": "SHA256SUMS", "browser_download_url": "https://example.com/SHA256SUMS"},
    ]
    payload = {"tag_name": "v0.3.0", "assets": assets}

    def get(url, timeout=None):
        return SimpleNamespace(status_code=200, json=lambda: payload)

    monkeypatch.setattr(release.requests, "get", get)

    def download(url, dest):
        if dest.name.endswith(".whl"):
            dest.write_bytes(WHEEL_BYTES)
        else:
            dest.write_text("{}  {}\n".format(WHEEL_SHA, WHEEL_NAME), encoding="utf-8")

    monkeypatch.setattr(installer, "_download", download)


@pytest.fixture
def fake_run(monkeypatch):
    def run(cmd, env=None):
        cmd = list(cmd)
        if len(cmd) >= 3 and cmd[1] == "-m" and cmd[2] == "venv":
            venv_dir = Path(cmd[3])
            (venv_dir / "bin").mkdir(parents=True, exist_ok=True)
            (venv_dir / "bin" / "pip").touch()
            return _result()
        if len(cmd) >= 2 and cmd[-1] == "--version":
            return _result(stdout="printlabelms 0.3.0\n")
        if len(cmd) >= 3 and cmd[1] == "-c":
            return _result()
        if len(cmd) >= 2 and cmd[-1] == "freeze":
            return _result(stdout="printlabelms==0.3.0\n")
        if len(cmd) >= 2 and cmd[1] == "install":
            return _result()
        return _result()

    monkeypatch.setattr(installer, "_run", run)


def test_parse_version_and_compare():
    assert release.parse_version("v0.3.0") == (0, 3, 0)
    assert release.compare_versions((0, 2, 0), (0, 3, 0)) == -1
    assert release.compare_versions((0, 3, 0), (0, 3, 0)) == 0
    assert release.compare_versions((0, 4, 0), (0, 3, 0)) == 1
    with pytest.raises(updater.UpdaterError):
        release.parse_version("abc")


def test_select_wheel_and_asset():
    assets = [
        {"name": WHEEL_NAME, "browser_download_url": "https://example.com/{}".format(WHEEL_NAME)},
        {"name": "SHA256SUMS", "browser_download_url": "https://example.com/SHA256SUMS"},
    ]
    assert release.select_wheel(assets)["name"] == WHEEL_NAME
    assert release.select_asset(assets, "SHA256SUMS")["name"] == "SHA256SUMS"
    with pytest.raises(updater.UpdaterError):
        release.select_wheel([{"name": "other.whl"}])
    with pytest.raises(updater.UpdaterError):
        release.select_asset(assets, "missing")


def test_sha256_mismatch(tmp_path):
    wheel = tmp_path / WHEEL_NAME
    wheel.write_bytes(WHEEL_BYTES)
    good_sums = "{}  {}\n".format(WHEEL_SHA, WHEEL_NAME)
    installer._verify_sha256(wheel, good_sums)
    bad_sums = "0" * 64 + "  {}\n".format(WHEEL_NAME)
    with pytest.raises(updater.UpdaterError):
        installer._verify_sha256(wheel, bad_sums)


def test_update_success(env, installed, fake_release, fake_run, capsys):
    assert updater.update() == 0
    data = env["data"] / "printlabelms"
    assert _link_target(data / "current") == data / "versions" / "0.3.0"
    assert _link_target(data / "previous") == data / "versions" / "0.2.0"
    assert (data / "versions" / "0.3.0" / "venv").exists()
    snapshot = data / "versions" / "0.2.0" / "settings.json"
    assert snapshot.read_text(encoding="utf-8") == '{"schema_version": 2}'
    log_path = env["state"] / "printlabelms" / "update.log"
    assert log_path.exists()
    assert "update v0.2.0 -> 0.3.0" in log_path.read_text(encoding="utf-8")
    assert "Установлена версия 0.3.0" in capsys.readouterr().out


def test_update_check_only(env, installed, fake_release, capsys):
    assert updater.update(check_only=True) == 0
    out = capsys.readouterr().out
    assert "Доступна новая версия v0.3.0" in out
    data = env["data"] / "printlabelms"
    assert _link_target(data / "current") == data / "versions" / "0.2.0"


def test_update_dev_mode(env):
    with pytest.raises(updater.UpdaterError):
        updater.update()


def test_health_check_failure_keeps_current(env, installed, fake_release, monkeypatch):
    def run(cmd, env=None):
        cmd = list(cmd)
        if len(cmd) >= 3 and cmd[1] == "-m" and cmd[2] == "venv":
            venv_dir = Path(cmd[3])
            (venv_dir / "bin").mkdir(parents=True, exist_ok=True)
            (venv_dir / "bin" / "pip").touch()
            return _result()
        if len(cmd) >= 2 and cmd[-1] == "--version":
            return _result(returncode=1, stderr="health check failed")
        if len(cmd) >= 2 and cmd[-1] == "freeze":
            return _result(stdout="printlabelms==0.3.0\n")
        return _result()

    monkeypatch.setattr(installer, "_run", run)
    with pytest.raises(updater.UpdaterError):
        updater.update()
    data = env["data"] / "printlabelms"
    assert _link_target(data / "current") == data / "versions" / "0.2.0"
    versions = data / "versions"
    assert not [entry for entry in versions.iterdir() if "tmp" in entry.name]


def test_rollback(env, installed, fake_run):
    data = env["data"] / "printlabelms"
    old_dir = data / "versions" / "0.1.0"
    bin_dir = old_dir / "venv" / "bin"
    bin_dir.mkdir(parents=True)
    (bin_dir / "printlabelms").touch()
    (bin_dir / "python").touch()
    os.symlink(old_dir, data / "previous")
    (old_dir / "settings.json").write_text('{"schema_version": 2}', encoding="utf-8")
    config_file = env["config"] / "printlabelms" / "settings.json"
    config_file.write_text('{"schema_version": 9}', encoding="utf-8")
    assert updater.rollback() == 0
    assert _link_target(data / "current") == data / "versions" / "0.1.0"
    assert _link_target(data / "previous") == data / "versions" / "0.2.0"
    assert config_file.read_text(encoding="utf-8") == '{"schema_version": 2}'
    backups = list(config_file.parent.glob("settings.json.bak-rollback-*"))
    assert len(backups) == 1


def test_rollback_no_previous(env, installed):
    with pytest.raises(updater.UpdaterError):
        updater.rollback()


def test_rotation(env, installed, fake_release, fake_run):
    old_dir = env["data"] / "printlabelms" / "versions" / "0.1.0"
    (old_dir / "venv" / "bin").mkdir(parents=True)
    assert updater.update() == 0
    versions = env["data"] / "printlabelms" / "versions"
    names = sorted(entry.name for entry in versions.iterdir())
    assert names == ["0.2.0", "0.3.0"]
