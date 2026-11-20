from pathlib import Path

import config
from config import Config, Orientation

REPO_ROOT = Path(__file__).parent.parent


def test_read_config_example():
    cfg = config.read_config(REPO_ROOT / "settings_example.json")
    assert isinstance(cfg, Config)
    assert cfg.printer.name == "TSC TE200"
    assert cfg.printer.resolution == 600
    assert len(cfg.label_formats) == 2
    for label_format in cfg.label_formats:
        assert isinstance(label_format.orientation, Orientation)
