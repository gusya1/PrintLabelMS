from typing import List

from pydantic import BaseModel
from enum import Enum


class Orientation(str, Enum):
    PORTRAIT = "Portrait",
    LANDSCAPE = "Landscape"


class LabelFormat(BaseModel):
    width: int
    height: int
    width_offset: int
    height_offset: int
    orientation: Orientation


class PrinterConfig(BaseModel):
    name: str
    resolution: int


class Config(BaseModel):
    moy_sklad_token: str
    printer: PrinterConfig
    label_formats: List[LabelFormat]


def read_config(file_path):
    config_file = open(file_path, "r", encoding="utf-8")
    return Config.model_validate_json(config_file.read())
