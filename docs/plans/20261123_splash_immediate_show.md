# План: сплэш-экран открывается сразу и маскирует загрузку данных (TODO пункт 3)

Источник: TODO.md, пункт 3 — «На линукс spalsh screen открывается в последний
момент загрузки. Должен открываться сразу же и маскировать загрузку.»

## Проблема

В `_run_gui()` (`src/PrintLabelMS/__main__.py`) `splash.show()` вызывается до
загрузки данных, но цикл событий Qt стартует только с `app.exec()` — после всех
сетевых вызовов (`get_assortment`, `get_custom_templates`,
`get_organizations`). Qt рисует виджеты лишь при обработке событий, поэтому
сплэш реально появляется на экране после завершения загрузки — «в последний
момент».

## Решение

Вынести загрузку конфига и данных МойСклада в фоновый поток:
`app.exec()` стартует сразу после показа сплэша, цикл событий крутится во время
загрузки (сплэш маскирует её), по завершении `MainWindow` создаётся на главном
потоке через сигналы. Паттерн совпадает с `UpdateService`
(QObject + pyqtSignal + daemon-Thread). Асинхронный клиент МойСклада не
рассматривается: библиотека moy_skad v0.1.0 синхронная (requests.Session,
time.sleep в ретраях 429), асинхронность потребует переписать внешнюю
библиотеку и мост asyncio↔Qt без выигрыша — загрузка при старте это три
последовательных обхода API под лимитом 11 запросов/3с на токен.

## Файлы для модификации

- `src/PrintLabelMS/__main__.py`: `_run_gui` — app → `splash.show()` →
  коннекты `StartupLoader.loaded/error` → `loader.start()` →
  `return app.exec() or exit_code`. Слот `loaded`: `Converter`,
  `PrintHandler` (инициализация QPrinter только на главном потоке),
  `MainWindow`, `window.show()`, `splash.finish(window)`; исключение на этом
  этапе — `fatal_error` + код 1. Слот `error`:
  `gui.message_box.fatal_error` + код 1. Импорт `startup_loader` — ленивый,
  как остальные GUI-импорты (путь `--version` без Qt не ломается).
- `TODO.md`: удалить пункт 3.
- `docs/architecture.md`: «Ключевые классы и файлы» — строка про
  `src/PrintLabelMS/startup_loader.py`; шаг 2 «Поток данных» — загрузка при
  старте в фоновом потоке; из описания `__main__.py` убрать
  «загрузка данных МойСклада».
- `docs/gui.md`: раздел сплэша — загрузка идёт в фоновом потоке,
  сплэш маскирует её.

## Файлы для создания

- `src/PrintLabelMS/startup_loader.py`: `StartupLoader(QtCore.QObject)`;
  сигналы `loaded(object)` (бандл `(config_model, manager, assortment,
  templates, organization)`) и `error(str)`; `start()` — daemon-поток:
  `read_config(settings_path)` → `MoySkladManager(token)` →
  `get_assortment` / `get_custom_templates` / `get_organizations`
  (пустой список → `RuntimeError("Организация не найдена")`) →
  `loaded.emit(...)`; любое исключение → `error.emit(str(e))`. В потоке только
  конфиг и сеть, Qt-объекты не создаются.
- `tests/test_startup_loader.py`: QCoreApplication-фикстура +
  `_wait_for(processEvents)` (паттерн из test_update_service.py); monkeypatch
  `read_config` / `MoySkladManager`; тесты: успех (бандл в сигнале,
  организация — первая), нет организаций →
  `error("Организация не найдена")`, исключение в `read_config` /
  `get_assortment` → `error` с сообщением.

## Проверка

1) `pytest`; 2) `ruff check .`.

## Актуализация документации

`docs/architecture.md`, `docs/gui.md` (раздел сплэша), `TODO.md`
(удаление пункта 3).
