import gui.__build__ as build_module


def test_generate_ui_creates_output_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(build_module, "get_build_directory", lambda: tmp_path)
    build_module.generate_ui()
    output_file = tmp_path / "ui" / "mainwindow_ui.py"
    assert output_file.exists()
    assert "class Ui_MainWindow" in output_file.read_text(encoding="utf-8")
