import re

import requests

from updater import UpdaterError
from updater.paths import APP_NAME

REPO = "gusya1/PrintLabelMS"
API_BASE = "https://api.github.com/repos/{}/releases".format(REPO)


def parse_version(tag):
    
    match = re.fullmatch(r"v(\d+)\.(\d+)\.(\d+)", tag.strip())
    if not match:
        raise UpdaterError("Некорректный тег версии: {}".format(tag))
    return tuple(int(part) for part in match.groups())


def compare_versions(a, b):
    if a < b:
        return -1
    if a > b:
        return 1
    return 0


def fetch_latest_release():
    response = requests.get(API_BASE + "/latest", timeout=30)
    if response.status_code != 200:
        raise UpdaterError("Не удалось получить последний релиз (HTTP {})".format(response.status_code))
    return response.json()


def fetch_release_by_tag(tag):
    response = requests.get("{}/tags/{}".format(API_BASE, tag), timeout=30)
    if response.status_code != 200:
        raise UpdaterError("Релиз {} не найден (HTTP {})".format(tag, response.status_code))
    return response.json()


def select_asset(assets, name):
    for asset in assets:
        if asset.get("name") == name:
            return asset
    raise UpdaterError("Ассет {} отсутствует в релизе".format(name))


def select_wheel(assets):
    for asset in assets:
        name = asset.get("name", "")
        if name.startswith(APP_NAME + "-") and name.endswith("-py3-none-any.whl"):
            return asset
    raise UpdaterError("Wheel py3-none-any отсутствует в релизе")
