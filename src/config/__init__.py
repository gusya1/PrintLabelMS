from enum import StrEnum

from pydantic import BaseModel, Field


class Orientation(StrEnum):
    PORTRAIT = "Portrait",
    LANDSCAPE = "Landscape"


class LabelFormat(BaseModel):
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    width_offset: int = Field(ge=0)
    height_offset: int = Field(ge=0)
    orientation: Orientation


class PrinterConfig(BaseModel):
    name: str
    resolution: int = Field(gt=0)


class Config(BaseModel):
    moy_sklad_token: str
    poppler_path: str | None
    printer: PrinterConfig
    label_formats: list[LabelFormat]


def read_config(file_path):
    with open(file_path, encoding="utf-8") as config_file:
        return Config.model_validate_json(config_file.read())
