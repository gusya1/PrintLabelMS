import hashlib
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from updater import paths, release
from updater import UpdaterError


def _run(cmd, env=None):
    return subprocess.run(cmd, capture_output=True, text=True, env=env)


def _installed():
    link = paths.current_link()
    if not link.is_symlink():
        raise UpdaterError("PrintLabelMS не установлен (нет симлинка current)")
    return Path(os.readlink(link))


def _current_version():
    version_dir = _installed()
    try:
        return release.parse_version("v{}".format(version_dir.name))
    except UpdaterError as e:
        raise UpdaterError("Некорректное имя каталога версии: {}".format(version_dir.name)) from e


def _switch_link(link, target):
    link.parent.mkdir(parents=True, exist_ok=True)
    tmp = link.with_name(link.name + ".tmp-{}".format(os.getpid()))
    if tmp.exists() or tmp.is_symlink():
        os.remove(tmp)
    os.symlink(target, tmp)
    try:
        os.replace(tmp, link)
    except OSError:
        if link.is_symlink() or link.exists():
            os.remove(link)
        os.replace(tmp, link)


def _snapshot_config(version_dir):
    config_file = paths.config_path()
    if not config_file.exists():
        return
    version_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(config_file, version_dir / "settings.json")


def _health_check(venv_dir):
    result = _run([str(venv_dir / "bin" / "printlabelms"), "--version"])
    if result.returncode != 0:
        raise UpdaterError("Health-check --version провален: {}".format(result.stderr.strip()))
    env = dict(os.environ)
    env["QT_QPA_PLATFORM"] = "offscreen"
    result = _run([str(venv_dir / "bin" / "python"), "-c", "import gui.ui.mainwindow_ui"], env=env)
    if result.returncode != 0:
        raise UpdaterError("Health-check импорта UI провален: {}".format(result.stderr.strip()))


def _verify_sha256(wheel_path, sums_text):
    expected = None
    for line in sums_text.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1].strip("*") == wheel_path.name:
            expected = parts[0]
    if expected is None:
        raise UpdaterError("Контрольная сумма {} не найдена в SHA256SUMS".format(wheel_path.name))
    actual = hashlib.sha256(wheel_path.read_bytes()).hexdigest()
    if actual != expected.lower():
        raise UpdaterError("SHA256 не совпадает для {}".format(wheel_path.name))


def _download(url, dest):
    import requests

    response = requests.get(url, timeout=300)
    if response.status_code != 200:
        raise UpdaterError("Не удалось скачать {} (HTTP {})".format(url, response.status_code))
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(response.content)


def _rotate(keep):
    versions_dir = paths.versions_dir()
    if not versions_dir.exists():
        return
    entries = []
    for entry in versions_dir.iterdir():
        try:
            version = release.parse_version("v{}".format(entry.name))
        except UpdaterError:
            continue
        entries.append((version, entry))
    entries.sort(key=lambda item: item[0], reverse=True)
    for _, entry in entries[keep:]:
        shutil.rmtree(entry)


def update(target_version=None, check_only=False):
    version_dir = _installed()
    current = _current_version()
    if target_version is not None:
        tag = "v{}".format(target_version)
        parsed = release.parse_version(tag)
        info = release.fetch_release_by_tag(tag)
    else:
        info = release.fetch_latest_release()
        tag = info.get("tag_name", "")
        parsed = release.parse_version(tag)
    if check_only:
        if release.compare_versions(parsed, current) > 0:
            print("Доступна новая версия {}".format(tag))
        else:
            print("Установлена последняя версия v{}".format(".".join(str(part) for part in current)))
        return 0
    if parsed == current:
        print("Версия {} уже установлена".format(tag))
        return 0
    _snapshot_config(version_dir)
    cache = paths.cache_dir()
    cache.mkdir(parents=True, exist_ok=True)
    wheel_asset = release.select_wheel(info.get("assets", []))
    sums_asset = release.select_asset(info.get("assets", []), "SHA256SUMS")
    wheel_path = cache / wheel_asset["name"]
    _download(wheel_asset["browser_download_url"], wheel_path)
    sums_path = cache / "SHA256SUMS"
    _download(sums_asset["browser_download_url"], sums_path)
    _verify_sha256(wheel_path, sums_path.read_text(encoding="utf-8"))
    versions_dir = paths.versions_dir()
    target_name = "{}.{}.{}".format(*parsed)
    final_dir = versions_dir / target_name
    if final_dir.exists():
        shutil.rmtree(final_dir)
    tmp_dir = versions_dir / "{}.tmp-{}".format(target_name, os.getpid())
    venv_dir = tmp_dir / "venv"
    _run(["python3", "-m", "venv", str(venv_dir)])
    if not (venv_dir / "bin" / "pip").exists():
        raise UpdaterError("Не удалось создать venv")
    result = _run([str(venv_dir / "bin" / "pip"), "install", "--upgrade", str(wheel_path)])
    if result.returncode != 0:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise UpdaterError("pip install провален: {}".format(result.stderr.strip()))
    try:
        _health_check(venv_dir)
    except Exception as e:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise UpdaterError(str(e)) from e
    os.rename(tmp_dir, final_dir)
    old_target = version_dir
    _switch_link(paths.previous_link(), old_target)
    _switch_link(paths.current_link(), final_dir)
    _rotate(2)
    log_path = paths.update_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    freeze = _run([str(final_dir / "venv" / "bin" / "pip"), "freeze"])
    with open(log_path, "a", encoding="utf-8") as log_file:
        log_file.write("{} update v{} -> {}\n{}\n".format(
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ".".join(str(part) for part in current),
            target_name,
            freeze.stdout.strip(),
        ))
    print("Установлена версия {}".format(target_name))
    return 0


def rollback():
    version_dir = _installed()
    previous_link = paths.previous_link()
    if not previous_link.is_symlink():
        raise UpdaterError("Нет предыдущей версии для отката")
    old_target = Path(os.readlink(previous_link))
    config_file = paths.config_path()
    backup_path = None
    if config_file.exists():
        backup_path = config_file.with_name(
            "settings.json.bak-rollback-{}".format(datetime.now().strftime("%Y%m%d-%H%M%S"))
        )
        shutil.copyfile(config_file, backup_path)
    snapshot = old_target / "settings.json"
    if snapshot.exists():
        config_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(snapshot, config_file)
    else:
        print("Снимок конфига предыдущей версии не найден — текущий конфиг сохранён", file=sys.stderr)
    try:
        _health_check(old_target / "venv")
    except Exception as e:
        if backup_path is not None and config_file.exists():
            shutil.copyfile(backup_path, config_file)
        raise UpdaterError(str(e)) from e
    _switch_link(paths.current_link(), old_target)
    _switch_link(previous_link, version_dir)
    print("Откат на версию {}".format(old_target.name))
    return 0
