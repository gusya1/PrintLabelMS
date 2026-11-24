from pathlib import Path

from PrintLabelMS.__main__ import _default_settings_path, main


def test_version(capsys):
    assert main(["--version"]) == 0
    out = capsys.readouterr().out
    for line in ("printlabelms", "Python", "PyQt5", "pydantic", "pypdfium2"):
        assert line in out


def test_update_not_installed(capsys, monkeypatch, tmp_path):
    for var in ("XDG_DATA_HOME", "XDG_CONFIG_HOME", "XDG_STATE_HOME", "XDG_CACHE_HOME"):
        monkeypatch.setenv(var, str(tmp_path / var.lower()))
    assert main(["update"]) != 0
    err = capsys.readouterr().err
    assert "не установлен" in err


def test_rollback_not_installed(capsys, monkeypatch, tmp_path):
    for var in ("XDG_DATA_HOME", "XDG_CONFIG_HOME", "XDG_STATE_HOME", "XDG_CACHE_HOME"):
        monkeypatch.setenv(var, str(tmp_path / var.lower()))
    assert main(["rollback"]) != 0
    err = capsys.readouterr().err
    assert "не установлен" in err


def test_kiosk_flag_passed_to_gui(monkeypatch):
    calls = []

    def fake_run_gui(settings_path, kiosk=False):
        calls.append((settings_path, kiosk))
        return 0

    monkeypatch.setattr("PrintLabelMS.__main__._run_gui", fake_run_gui)
    assert main(["settings.json", "--kiosk"]) == 0
    assert main(["settings.json"]) == 0
    assert calls == [(Path("settings.json"), True), (Path("settings.json"), False)]


def test_default_settings_path_xdg(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    assert _default_settings_path() == tmp_path / "printlabelms" / "settings.json"


def test_default_settings_path_home(monkeypatch):
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    path = _default_settings_path()
    assert path.name == "settings.json"
    assert path.parent.name == "printlabelms"
