from pathlib import Path

import config
import pytest
from config import Config, Orientation
from pydantic import ValidationError

REPO_ROOT = Path(__file__).parent.parent


def test_read_config_example():
    cfg = config.read_config(REPO_ROOT / "settings_example.json")
    assert isinstance(cfg, Config)
    assert cfg.printer.name == "TSC TE200"
    assert cfg.printer.resolution == 600
    assert len(cfg.label_formats) == 2
    for label_format in cfg.label_formats:
        assert isinstance(label_format.orientation, Orientation)


def test_label_format_zero_size_invalid():
    with pytest.raises(ValidationError):
        config.LabelFormat(width=0, height=40, width_offset=0, height_offset=0, orientation=config.Orientation.PORTRAIT)


def test_label_format_negative_offset_valid():
    label_format = config.LabelFormat(
        width=58, height=40, width_offset=-1, height_offset=-2, orientation=config.Orientation.PORTRAIT
    )
    assert label_format.width_offset == -1
    assert label_format.height_offset == -2


def test_printer_config_zero_resolution_invalid():
    with pytest.raises(ValidationError):
        config.PrinterConfig(name="TSC TE200", resolution=0)
