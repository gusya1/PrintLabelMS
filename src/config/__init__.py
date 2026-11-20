from enum import StrEnum

from pydantic import BaseModel


class Orientation(StrEnum):
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
    poppler_path: str | None
    printer: PrinterConfig
    label_formats: list[LabelFormat]


def read_config(file_path):
    config_file = open(file_path, encoding="utf-8")
    return Config.model_validate_json(config_file.read())
