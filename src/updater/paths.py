import os
from pathlib import Path

# Совпадает с name в pyproject.toml и [project.scripts]
APP_NAME = "printlabelms"


def data_dir():
    return Path(os.environ.get("XDG_DATA_HOME") or "~/.local/share").expanduser() / APP_NAME


def versions_dir():
    return data_dir() / "versions"


def current_link():
    return data_dir() / "current"


def previous_link():
    return data_dir() / "previous"


def config_path():
    base = Path(os.environ.get("XDG_CONFIG_HOME") or "~/.config").expanduser()
    return base / APP_NAME / "settings.json"


def state_dir():
    return Path(os.environ.get("XDG_STATE_HOME") or "~/.local/state").expanduser() / APP_NAME


def update_log_path():
    return state_dir() / "update.log"


def cache_dir():
    return Path(os.environ.get("XDG_CACHE_HOME") or "~/.cache").expanduser() / APP_NAME
