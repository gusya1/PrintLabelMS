import importlib.metadata
import os
from pathlib import Path
from threading import Thread

from PyQt5 import QtCore

import updater


class UpdateService(QtCore.QObject):

    """Фоновая проверка новой версии и выполнение update/rollback."""

    update_available = QtCore.pyqtSignal(str)
    progress_changed = QtCore.pyqtSignal(str, int)
    finished = QtCore.pyqtSignal(bool, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._check_thread = None
        self._update_thread = None

    @property
    def installed(self):
        return updater.paths.current_link().is_symlink()

    def current_version(self):
        """Версия активной установки: из симлинка current, иначе из метаданных пакета."""
        try:
            return "v{}.{}.{}".format(*self.__current_version())
        except Exception:
            pass
        try:
            return "v{}".format(importlib.metadata.version(updater.paths.APP_NAME))
        except importlib.metadata.PackageNotFoundError:
            return "unknown"

    def start_check(self):
        if not self.installed:
            return
        self._check_thread = Thread(target=self.__check_worker, daemon=True)
        self._check_thread.start()

    def update(self, target_version=None):
        self._update_thread = Thread(target=self.__update_worker, args=(target_version,), daemon=True)
        self._update_thread.start()

    def rollback(self):
        self._update_thread = Thread(target=self.__rollback_worker, daemon=True)
        self._update_thread.start()

    def __check_worker(self):
        try:
            info = updater.release.fetch_latest_release()
            tag = info.get("tag_name", "")
            if self.__is_newer(tag):
                self.update_available.emit(tag)
        except Exception:
            pass

    def __current_version(self):
        current_dir = Path(os.readlink(updater.paths.current_link()))
        return updater.parse_version("v{}".format(current_dir.name))

    def __is_newer(self, tag):
        try:
            new = updater.parse_version(tag)
            current = self.__current_version()
        except Exception:
            return False
        return updater.compare_versions(new, current) > 0

    def __update_worker(self, target_version):
        try:
            updater.update(target_version=target_version)
            self.progress_changed.emit("Обновление завершено", 3)
            self.finished.emit(True, "")
        except Exception as e:
            self.finished.emit(False, str(e))

    def __rollback_worker(self):
        try:
            updater.rollback()
            self.finished.emit(True, "")
        except Exception as e:
            self.finished.emit(False, str(e))
