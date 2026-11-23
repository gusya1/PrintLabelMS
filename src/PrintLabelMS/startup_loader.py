from threading import Thread

from PyQt5 import QtCore

from config import read_config
from moysklad_manager.manager import MoySkladManager


class StartupLoader(QtCore.QObject):

    """Загрузка конфига и данных МойСклада в фоновом потоке при старте."""

    loaded = QtCore.pyqtSignal(object)
    error = QtCore.pyqtSignal(str)

    def __init__(self, settings_path, parent=None):
        super().__init__(parent)
        self.__settings_path = settings_path
        self.__thread = None

    def start(self):
        self.__thread = Thread(target=self.__worker, daemon=True)
        self.__thread.start()

    def __worker(self):
        try:
            config_model = read_config(self.__settings_path)
            manager = MoySkladManager(config_model.moy_sklad_token)
            assortment = manager.get_assortment()
            templates = manager.get_custom_templates()
            organizations = manager.get_organizations()
            if not organizations:
                raise RuntimeError("Организация не найдена")
            self.loaded.emit((config_model, manager, assortment, templates, organizations[0]))
        except Exception as e:
            self.error.emit(str(e))
