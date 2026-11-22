import json
from pathlib import Path

import config
import pytest
from config import Config


def _write_old_config(path: Path) -> dict:
    raw = {
        "moy_sklad_token": "00000000000000000000000000000000000",
        "printer": {"name": "TSC TE200", "resolution": 600},
        "poppler_path": "build/windows/external/poppler-25.07.0/Library/bin",
        "label_formats": [
            {"width": 58, "height": 40, "width_offset": 0, "height_offset": 0, "orientation": "Portrait"},
            {"width": 74, "height": 120, "width_offset": 0, "height_offset": 0, "orientation": "Landscape"},
        ],
    }
    with open(path, "w", encoding="utf-8") as config_file:
        json.dump(raw, config_file, indent=2)
    return raw


def test_read_config_old_format_without_schema_version(tmp_path):
    config_file = tmp_path / "settings.json"
    _write_old_config(config_file)
    cfg = config.read_config(str(config_file))
    assert isinstance(cfg, Config)
    assert cfg.schema_version == 2
    assert cfg.check_updates is True


def test_migration_removes_poppler_path_from_file(tmp_path):
    config_file = tmp_path / "settings.json"
    _write_old_config(config_file)
    config.read_config(str(config_file))
    data = json.loads(config_file.read_text(encoding="utf-8"))
    assert "poppler_path" not in data


def test_backup_created_with_old_raw(tmp_path):
    config_file = tmp_path / "settings.json"
    _write_old_config(config_file)
    config.read_config(str(config_file))
    backups = list(tmp_path.glob("settings.json.bak-*"))
    assert len(backups) == 1
    backup_data = json.loads(backups[0].read_text(encoding="utf-8"))
    assert "poppler_path" in backup_data


def test_newer_schema_version_raises(tmp_path):
    config_file = tmp_path / "settings.json"
    raw = _write_old_config(config_file)
    raw["schema_version"] = 99
    with open(config_file, "w", encoding="utf-8") as file_handle:
        json.dump(raw, file_handle, indent=2)
    with pytest.raises(ValueError, match="более новой версией"):
        config.read_config(str(config_file))


def test_reread_migrated_config_creates_no_new_backup(tmp_path):
    config_file = tmp_path / "settings.json"
    _write_old_config(config_file)
    config.read_config(str(config_file))
    backups_before = list(tmp_path.glob("settings.json.bak-*"))
    config.read_config(str(config_file))
    backups_after = list(tmp_path.glob("settings.json.bak-*"))
    assert len(backups_after) == len(backups_before)


def test_check_updates_default_true(tmp_path):
    config_file = tmp_path / "settings.json"
    _write_old_config(config_file)
    cfg = config.read_config(str(config_file))
    assert cfg.check_updates is True
