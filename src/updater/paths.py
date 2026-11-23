import os
from pathlib import Path


def data_dir():
    return Path(os.environ.get("XDG_DATA_HOME") or "~/.local/share").expanduser() / "printlabelms"


def versions_dir():
    return data_dir() / "versions"


def current_link():
    return data_dir() / "current"


def previous_link():
    return data_dir() / "previous"


def config_path():
    base = Path(os.environ.get("XDG_CONFIG_HOME") or "~/.config").expanduser()
    return base / "printlabelms" / "settings.json"


def state_dir():
    return Path(os.environ.get("XDG_STATE_HOME") or "~/.local/state").expanduser() / "printlabelms"


def update_log_path():
    return state_dir() / "update.log"


def cache_dir():
    return Path(os.environ.get("XDG_CACHE_HOME") or "~/.cache").expanduser() / "printlabelms"
