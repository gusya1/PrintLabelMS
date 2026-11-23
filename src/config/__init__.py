import json
import os
from datetime import datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field

from config.migrations import CURRENT_SCHEMA_VERSION as CURRENT_SCHEMA_VERSION, migrate


class Orientation(StrEnum):
    PORTRAIT = "Portrait"
    LANDSCAPE = "Landscape"


class LabelFormat(BaseModel):
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    width_offset: int
    height_offset: int
    orientation: Orientation


class PrinterConfig(BaseModel):
    name: str
    resolution: int = Field(gt=0)


class Config(BaseModel):
    schema_version: int = 1
    moy_sklad_token: str
    check_updates: bool = True
    ui_scale: float = Field(default=1.0, gt=0)
    printer: PrinterConfig
    label_formats: list[LabelFormat]


def read_config(file_path):
    file_path = Path(file_path)
    with open(file_path, encoding="utf-8") as config_file:
        raw = json.load(config_file)
    migrated = migrate(raw)
    if migrated != raw:
        backup_path = "{}.bak-{}".format(file_path, datetime.now().strftime("%Y%m%d-%H%M%S"))
        with open(backup_path, "w", encoding="utf-8") as backup_file:
            json.dump(raw, backup_file, indent=2)
        tmp_path = file_path.parent / (file_path.name + ".tmp")
        with open(tmp_path, "w", encoding="utf-8") as config_file:
            json.dump(migrated, config_file, indent=2)
        os.replace(tmp_path, file_path)
    return Config.model_validate(migrated)
