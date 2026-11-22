# План: быстрая установка и обновление на Linux (Lubuntu 26.04)

Источник: согласованные решения grilling-сессии 2026-11-22.
Целевая ОС — Lubuntu 26.04 LTS (Python 3.14, LXQt); установка — в домашний
каталог пользователя, без системных пакетов Python и без sudo (кроме
опциональной установки `python3-venv`).

## Решения (согласовано с пользователем, 2026-11-22)

| Вопрос | Решение |
| --- | --- |
| Права и область | Установка в `~/.local`, без sudo; Linux сейчас, механизм пригоден для Windows позже |
| Дистрибутив | Lubuntu 26.04 как гарантированная цель; другие — по возможности |
| Форма поставки | `install.sh` + изолированный venv + launcher + `.desktop` (не AppImage, не `.deb`, не pipx) |
| Обновление | Явная команда `printlabelms update` + ненавязчивая проверка в GUI (статус-бар, раз в 24 ч) |
| Киоск | Не реализуем |
| Удаление | Отдельной команды нет; повторный `install.sh --force` переустанавливает |
| Python | Системный `python3` (3.14) + venv, проверка `>= 3.12`; свой интерпретатор не поставляем |
| Конфиг | `~/.config/printlabelms/settings.json`; создаётся при установке, установщиком при обновлении не перезаписывается; CLI-аргумент — необязательный override |
| Миграции конфига | `schema_version` + последовательные миграции (допускаются любые изменения схемы); перед обновлением активный конфиг сохраняется в каталог старой версии, `rollback` восстанавливает его |
| Источник обновлений | GitHub Releases по тегам `vX.Y.Z`; git у оператора не нужен |
| Артефакт | wheel `py3-none-any` с уже сгенерированным `gui/ui/` |
| Зависимость moy_sklad | Остаётся git-ссылкой; инсталлятор проверяет наличие `git` |
| Lockfile | Не используем (решение Q6=b); зависимости ставятся по диапазонам `pyproject.toml` |
| Poppler | Заменяем pdf2image/poppler на `pypdfium2` + Pillow; внешний бинарник и poppler-скрипты не нужны |
| `poppler_path` | Удаляется из модели и конфига миграцией; откат использует снимок конфига старой версии |
| Раскладка версий | `versions/<X.Y.Z>/venv` + симлинк `current`; health-check; автооткат; храним две версии |
| GUI-уведомление | Статус-бар с кнопкой «Обновить»; кнопка запускает обновление и перезапуск |
| Диагностика | `--version` печатает версии; updater пишет `pip freeze` в лог |
| Wayland | Launcher не форсирует платформу Qt; `QT_QPA_PLATFORM=xcb` — документированный fallback |
| Первый релиз | Версия `0.3.0`, тег `v0.3.0`; ассеты: wheel, `install.sh`, `SHA256SUMS` |
| План | этот файл |

## Раскладка установки

```
~/.local/share/printlabelms/
  versions/<X.Y.Z>/venv/        # изолированное окружение версии
  versions/<X.Y.Z>/settings.json  # снимок конфига на момент обновления
  current -> versions/<X.Y.Z>   # активная версия
  previous -> versions/<X.Y.Z>  # предыдущая (для rollback)
  icon.png                      # стабильный путь для .desktop
~/.local/bin/printlabelms       # симлинк на current/bin/printlabelms
~/.local/share/applications/printlabelms.desktop
~/.config/printlabelms/settings.json
~/.local/state/printlabelms/update.log
~/.cache/printlabelms/          # скачанные wheel и кэш проверки обновлений
```

Каталоги вычисляются по XDG-переменным с указанными значениями по умолчанию.
Приложение считается «установленным», если существует симлинк `current`;
в dev-режиме (запуск из репозитория) команды обновления недоступны, а
уведомление в GUI не показывается.

## Контракты

### Конфиг (`src/config/__init__.py`)

```python
class Config(BaseModel):
    schema_version: int = 1
    moy_sklad_token: str
    check_updates: bool = True
    printer: PrinterConfig
    label_formats: list[LabelFormat]
```

- `read_config(path)` читает сырой JSON, применяет миграции, валидирует модель,
  при изменении схемы атомарно перезаписывает файл и оставляет бэкап
  `settings.json.bak-<YYYYMMDD-HHMMSS>`.
- `schema_version` новее поддерживаемой → понятная ошибка (конфиг от более
  новой версии).
- Шаблон, который пишет `install.sh`: `schema_version: 1`,
  `check_updates: true`, плейсхолдеры токена и принтера, форматы этикеток
  как в `settings_example.json`.

### Миграции (`src/config/migrations.py`)

- `CURRENT_SCHEMA_VERSION`;
- `MIGRATIONS: dict[int, Callable[[dict], dict]]` — миграция `N → N+1`;
- `migrate(raw: dict) -> dict` применяет цепочку последовательно;
- отсутствие `schema_version` трактуется как `1`;
- миграции могут добавлять, удалять и переименовывать поля: перед обновлением
  конфиг старой версии сохраняется в `versions/<old>/settings.json`, поэтому
  откат не зависит от обратимости миграций; перед перезаписью конфига при
  миграции создаётся бэкап `settings.json.bak-<timestamp>`.

### CLI (`src/PrintLabelMS/__main__.py`)

`[project.scripts] printlabelms = "PrintLabelMS.__main__:main"`.

```
printlabelms [settings.json]        # GUI, по умолчанию ~/.config/printlabelms/settings.json
printlabelms --version              # версии приложения, Python, PyQt5, pydantic, pypdfium2
printlabelms update [--to X.Y.Z] [--check]
printlabelms rollback
```

- Импорт PyQt5 — только в ветке запуска GUI, чтобы `--version`/`update`
  работали без создания `QApplication`.
- `--check` только проверяет наличие новой версии и печатает результат.
- Ошибки CLI — в stderr, код возврата ≠ 0.

### Обновление (`src/updater/`)

- `paths.py` — XDG-пути, `current`/`previous`, каталог версий;
- `release.py` — GitHub API (`/releases/latest`, `/releases/tags/vX.Y.Z`),
  разбор `tag_name` и ассетов, сравнение версий, игнорирование prerelease;
- `installer.py` — скачивание wheel и `SHA256SUMS` в кэш, проверка SHA256,
  создание venv, `pip install <wheel>`, health-check, переключение симлинков,
  ротация версий, лог;
- `__init__.py` — публичные `update`, `rollback`, `check`, `UpdaterError`.

Правила установки версии:

1. Сохранить активный конфиг в каталог текущей (заменяемой) версии:
   `versions/<текущая>/settings.json`; это снимок, который вернёт `rollback`.
2. Скачать wheel и контрольные суммы, проверить SHA256.
3. Создать `versions/<X.Y.Z>.tmp-<pid>/venv` через `python3 -m venv`.
4. `venv/bin/pip install --upgrade <wheel>` (зависимости, включая git-ссылку
   `moy_sklad`, разрешает pip).
5. Health-check: `venv/bin/printlabelms --version` и импорт
   `gui.ui.mainwindow_ui` с `QT_QPA_PLATFORM=offscreen`.
6. Атомарно переименовать каталог и переключить `current`; старый `current`
   становится `previous`; каталоги старше двух версий удалить вместе с их
   снимками конфига.
7. При любой ошибке удалить временный каталог, `current` и активный конфиг
   не трогать.
8. После успеха дописать в `update.log` версии и `pip freeze`.

`rollback` сохраняет текущий конфиг как
`settings.json.bak-rollback-<timestamp>`, восстанавливает
`versions/<previous>/settings.json` в `~/.config/printlabelms/settings.json`
(если снимка нет — оставляет текущий конфиг и выводит предупреждение), затем
переключает `current` на `previous` (health-check обязателен; при его провале
возвращаются прежние `current` и конфиг).
Обновление не выполняется при активной печати; после успеха GUI
перезапускает приложение через `QProcess.startDetached`.

## Файлы для создания

- `scripts/install.sh` — бутстрап: preflight, установка последнего релиза,
  конфиг, launcher, `.desktop`, иконка; при уже установленной версии
  делегирует `current/bin/printlabelms update`; флаги `--version X.Y.Z`,
  `--force`, `--help`;
- `src/updater/__init__.py`, `paths.py`, `release.py`, `installer.py`;
- `src/config/migrations.py`;
- `tests/test_updater.py` — сравнение версий, выбор ассетов, SHA256,
  раскладка версий, снимок и восстановление конфига, ротация;
- `tests/test_config_migrations.py` — отсутствие `schema_version`,
  последовательные миграции, удаление `poppler_path`, бэкап, будущая версия,
  запись конфига;
- `tests/test_cli.py` — `--version`, код возврата, путь к конфигу по умолчанию.

## Файлы для модификации

- `pyproject.toml`:
  - `version = "0.3.0"`;
  - убрать `pdf2image`, добавить `pypdfium2>=5.15`, `Pillow>=12`;
  - `[project.scripts] printlabelms`;
  - `src/updater` в packages;
  - `build` в dev-зависимости (для CI-сборки wheel).
- `src/PrintLabelMS/__main__.py` — `main()`, argparse, ленивый импорт Qt,
  путь к конфигу по умолчанию, подкоманды updater.
- `src/config/__init__.py` — новые поля, миграции, атомарная запись.
- `src/pdf_to_image_converter/converter.py` — pypdfium2:
  `scale = resolution / 72`, `bitmap.to_pil()`, сохранение в JPEG;
  `Converter()` без `poppler_path`; ошибки PDFium → `ConvertError`.
- `src/gui/MainWindow.py` — статус-бар, фоновая проверка обновлений
  (раз в 24 ч, кэш в `~/.cache`), кнопка «Обновить», прогресс, перезапуск.
- `src/gui/mainwindow.ui` — `QStatusBar`; после правки — регенерация
  `src/gui/ui/` (`python src/gui/__build__.py`).
- `tests/test_converter.py` — валидный минимальный PDF → JPEG, битый PDF →
  `ConvertError`, масштаб по DPI.
- `.github/workflows/ci.yml` — job сборки wheel и smoke-теста; job релиза
  по тегу (проверка версии, `SHA256SUMS`, GitHub Release).
- `settings_example.json` — `schema_version`, `check_updates`.
- `README.md`, `AGENTS.md`, `docs/architecture.md` — см. раздел документации.
- `TODO.md` — закрыть пункт про тег.

## Файлы для удаления

- `scripts/download_poppler_linux.sh`;
- `scripts/download_poppler_windows.bat`;
- зависимость `pdf2image` и все упоминания poppler в активной документации.

## Тесты

- `tests/test_converter.py`: минимальный PDF (байты в тесте) → JPEG
  (сигнатура `\xff\xd8`), масштаб 72 pt при 144 dpi → 144 px, битые данные →
  `ConvertError`.
- `tests/test_config_migrations.py`: миграция без `schema_version`; цепочка
  миграций; бэкап и атомарная запись; отказ при будущей версии; дефолты
  новых полей.
- `tests/test_updater.py`: сравнение версий, URL релиза и ассетов, проверка
  SHA256, успешная установка в tmp-каталог (venv и pip подменяются),
  снимок конфига перед обновлением и его восстановление при `rollback`,
  провал health-check → `current` не меняется, `rollback`, ротация двух
  версий, dev-режим → `UpdaterError`.
- `tests/test_cli.py`: `--version` содержит версии, `update` без установки
  возвращает ошибку, путь к конфигу по умолчанию.
- GUI-тесты не добавляются; GUI проверяется smoke-тестом CI и вручную.

## CI и релиз

- На PR и push в master: существующие pytest/ruff + сборка wheel
  (с генерацией `gui/ui/`) + smoke: чистый venv Python 3.14,
  `pip install dist/*.whl`, `printlabelms --version`, импорт UI при
  `QT_QPA_PLATFORM=offscreen`.
- На тег `v*`: проверка, что тег совпадает с `version` в `pyproject.toml`;
  сборка wheel; `install.sh`; `SHA256SUMS`; публикация GitHub Release
  (permissions `contents: write`).
- Ассеты релиза: `printlabelms-<ver>-py3-none-any.whl`, `install.sh`,
  `SHA256SUMS`. `requirements.txt` не публикуется (lockfile не используется).

## Срезы (по одному субагенту за раз)

1. Конвертер: pypdfium2 + Pillow, зависимости, тесты; удаление pdf2image
   и poppler-скриптов из активного кода.
2. Конфиг: `schema_version`, миграции, бэкап, дефолтный путь, шаблон,
   тесты.
3. CLI: entry point, `main()`, argparse, `--version`, подкоманды-заглушки,
   тесты.
4. Updater: пути, релизы, установка, health-check, откат, ротация, лог,
   тесты.
5. GUI: статус-бар, проверка обновлений, кнопка, перезапуск; регенерация UI.
6. `install.sh`: preflight, установка, конфиг, launcher, `.desktop`, иконка,
   идемпотентность, `--force`.
7. CI и релиз: сборка, smoke, job по тегу, версия `0.3.0`, тег `v0.3.0`.
8. Документация, `TODO.md`, приёмка на Lubuntu 26.04.

## Проверка

После каждого среза: 1) `pytest`; 2) `ruff check .`.
Для срезов 1–4 дополнительно: импорт изменённых модулей.
Срез 5: регенерация `gui/ui/` + оффскрин-импорт GUI.
Срез 6: `bash -n scripts/install.sh`, установка в чистый HOME
(`HOME=$(mktemp -d)`), повторный запуск, `--force`.
Срез 7: smoke-тест wheel в чистом venv Python 3.14.
Срез 8 (ручная приёмка на Lubuntu 26.04): установка one-liner, запуск,
печать реальной этикетки, проверка обновления, `rollback`, поведение под
Wayland/XWayland.

## Риски

- pypdfium2 рендерит иначе, чем poppler: возможны отличия в качестве
  печати — обязательна приёмка на реальном принтере; при проблемах
  остаётся возможность вернуть pdf2image отдельным решением.
- Без lockfile зависимости могут «уплыть» после обновления — смягчается
  логом `pip freeze` и `--version`; при инциденте — `rollback`.
- `curl | bash` неудобен для интерактивного sudo и небезопасен по своей
  природе — документируется ручной путь со скачиванием и проверкой SHA256.
- GitHub API без токена ограничен (60 запросов/час) — проверка не чаще
  раза в 24 часа и кэш; при ошибке сети уведомление молчит.
- Wayland на Lubuntu 26.04 не проверен фактами: launcher не форсирует
  платформу, `QT_QPA_PLATFORM=xcb` описан как fallback.
- `pip install` тянет `moy_sklad` из git: нужны `git` и сеть; preflight
  проверяет и выдаёт понятную ошибку.
- wheel без `gui/ui/` сломает установку — ловится smoke-тестом CI.
- Переключение симлинка при запущенном приложении требует перезапуска;
  обновление не запускается во время печати.
- Откат конфига опирается на снимок в каталоге версии: правки, сделанные
  на новой версии, сохраняются в бэкапе, но активным становится конфиг
  старой версии; при отсутствии снимка откатывается только код.

## Актуализация документации

- `README.md` — установка на Linux одной командой, обновление, откат,
  расположение конфига, отсутствие poppler.
- `AGENTS.md` — стек (pypdfium2/Pillow вместо pdf2image), карта проекта
  (`src/updater`, `scripts/install.sh`, `src/config/migrations.py`),
  удаление poppler-скриптов, порядок релиза.
- `docs/architecture.md` — конвертация через pypdfium2, поток обновления,
  снимки конфига и откат, миграции конфига, точки входа правил.
- `settings_example.json` — `schema_version`, `check_updates`.
- `TODO.md` — тег закрывается релизом `v0.3.0`.

История решений остаётся в этом плане.
