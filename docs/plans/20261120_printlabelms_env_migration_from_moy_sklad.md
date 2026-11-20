# План: перенос и адаптация файлов окружения из moy_sklad в PrintLabelMS

Источник конвенций окружения: `D:\ProjectsPy\moy_sklad` (AGENTS.md, pyproject.toml, .gitignore,
.vscode/settings.json, .github/workflows/ci.yml).

## Цель

Перенести в `D:\ProjectsPy\PrintLabelMS` и адаптировать под приложение файлы окружения из
`D:\ProjectsPy\moy_sklad`: AGENTS.md, pyproject.toml (единый источник зависимостей и
конфигурации инструментов), объединённый .gitignore, .vscode/settings.json, CI workflow,
README.md, docs/ и smoke-тесты. Убрать из git закоммиченные venv (~4000 файлов).
Код приложения не переписывать — только правки под ruff.

## Решения пользователя (согласовано)

| Вопрос | Решение |
| --- | --- |
| Q1. Сколькo файлов переносить | AGENTS.md, pyproject.toml, объединённый .gitignore, .vscode/settings.json; CI и README добавлены отдельными решениями (Q7/Q10); LICENSE не переносится |
| Q2. Роль pyproject.toml | Полное соответствие moy_sklad: `[project]` + зависимости из requirements.txt + dev-extra + tool.ruff/tool.pytest; hatchling с multi-package wheel, чтобы работал `pip install -e ".[dev]"`; requirements.txt удалить |
| Q3. Версия Python и пины | `requires-python >=3.12` (локально 3.13); пины в стиле moy_sklad: PyQt5>=5.15.6 (актуальный 5.15.11, abi3-колёса cp38+), pydantic>=2.11, requests>=2.32, pdf2image>=1.17.0; MSApi==0.2.11 остаётся (новых версий нет, sdist чистый Python); после миграции проверить импорты на 3.13 |
| Q4. .gitignore и закоммиченные venv | Слить gitignore; убрать из git оба venv (`git rm --cached`, ~4000 файлов), poppler оставить отслеживаемым (рантайм-зависимость); поправить start.bat (убрать хардкод `E:\`) |
| Q5. Конвенции AGENTS.md | Перенести все: docs/ + docs/plans/, версионирование тегами vX.Y.Z, правило «публичный репозиторий — никаких токенов и реальных данных» (токен в gitignored settings.json) |
| Q6. Тесты | Создать минимальные smoke-тесты сейчас, чтобы `pytest` реально проходил |
| Q7. CI workflow | Перенести и адаптировать: ruff + pytest на 3.12–3.14, триггер по ветке `master` (у PrintLabelMS дефолтная ветка master) |
| Q8. 8 ошибок ruff с конфигом moy_sklad | Поправить код под конфиг; конфиг держать идентичным moy_sklad |
| Q9. .env и PYTHONPATH | Удалить `.env` из репозитория и добавить в gitignore; импорты обеспечивает editable-установка |
| Q10. README.md | Написать короткий README по факту текущего состояния (поле `readme` в pyproject требует файл) |
| Q11. Метаданные [project] | name=printlabelms, version=0.1.0, author gusya1, без license-поля (приложение не публикуется на PyPI) |
| Q12. Коммиты и ветка | Несколько тематических коммитов прямо на `master` (5 коммитов, порядок ниже) |

## Файлы для создания

### 1. `pyproject.toml`

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "printlabelms"
version = "0.1.0"
description = "PyQt5-приложение: печать этикеток из МойСклада — ассортимент и шаблоны через MSApi, PDF→JPEG (poppler), печать на термопринтере"
readme = "README.md"
requires-python = ">=3.12"
authors = [{ name = "gusya1" }]
dependencies = [
    "PyQt5>=5.15.6",
    "MSApi==0.2.11",
    "pydantic>=2.11",
    "requests>=2.32",
    "pdf2image>=1.17.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=9.0",
    "ruff>=0.8",
]

[tool.hatch.build.targets.wheel]
packages = [
    "src/PrintLabelMS",
    "src/activity",
    "src/config",
    "src/gui",
    "src/moy_sklad",
    "src/pdf_to_image_converter",
    "src/resources",
]

[tool.ruff]
line-length = 121

[tool.ruff.lint]
select = [
    "E",
    "F",
    "UP",
    "D",
]
ignore = [
    "UP032",
    "D212",
    "D104",
    "D100",
    "D101",
    "D102",
    "D103",
    "D107",
    "D211",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

Ruff-конфиг идентичен `moy_sklad/pyproject.toml`. Зависимости — из requirements.txt с
обновлением нижних границ (Q3); MSApi закреплён ровно.

### 2. `AGENTS.md` (адаптация moy_sklad/AGENTS.md)

Структура и правила:

- **§1 Обзор проекта** — PrintLabelMS: самостоятельное PyQt5-приложение для печати этикеток
  из МойСклада: загрузка ассортимента, кастомных шаблонов этикеток и организации через MSApi;
  PDF-этикетка конвертируется в JPEG (poppler/pdf2image) и печатается на термопринтере.
  Стек: Python >=3.12; PyQt5>=5.15.6, MSApi==0.2.11, pydantic>=2.11, requests>=2.32,
  pdf2image>=1.17.0; сборка hatchling (editable-установка); тесты pytest; линт ruff
  (line-length 121).
- **§2 Окружение** — локальный venv `.venv` + `pip install -e ".[dev]"`; перед запуском GUI
  сгенерировать UI из форм: `python src/gui/__build__.py` (папка `gui/ui/` в gitignore);
  токен МойСклада хранится только в settings.json (gitignored), не в коде, git и фикстурах;
  версия приложения 0.1.0, релиз по тегу.
- **§3 Документация** — перенести как есть из moy_sklad §3 (docs/, docs/plans/ не редактируется
  и не удаляется, фактическое состояние без исторических оговорок, бизнес-логика и контракты
  данных, ключевые классы и файлы).
- **§4 Планирование** — перенести как есть из moy_sklad §4 (новые планы в
  docs/plans/<YYYYMMDD>_<name>.md, обязательный пункт «Актуализация документации»).
- **§5 Карта проекта** — src-layout:
  - `src/PrintLabelMS/__main__.py` — точка входа: QApplication, чтение settings.json,
    MSApi.set_access_token, загрузка ассортимента/шаблонов/организации, MainWindow;
  - `src/PrintLabelMS/print_handler.py` — `init_printer`, `get_qt_orientation`,
    `PrintHandler` (размер/ориентация/смещения/копии, print_pdf: JPEG → QPixmap → QPrinter);
  - `src/PrintLabelMS/exceptions.py` — AppError, MoySkladError;
  - `src/config/__init__.py` — pydantic-модели Config/PrinterConfig/LabelFormat/Orientation
    и read_config (settings.json);
  - `src/gui/MainWindow.py` — окно: список товаров с фильтром, выбор формата этикетки и
    шаблона, печать в фоне (threading + QProgressDialog), диалоги ошибок;
  - `src/gui/splash_screen.py`, `src/gui/message_box.py` — сплэш и фатальные ошибки;
  - `src/gui/__build__.py` — генерация `gui/ui/*_ui.py` из `.ui`-форм (PyQt5.uic);
    `mainwindow.ui` — исходная форма;
  - `src/moy_sklad/__init__.py` — тонкая обёртка над MSApi: get_assortment,
    get_assortment_custom_templates, get_organizations. Явная пометка: это НЕ пакет
    moy_sklad (D:\ProjectsPy\moy_sklad) — только адаптер над сторонним MSApi;
  - `src/pdf_to_image_converter/converter.py` — Converter.convert_pdf_to_jpeg
    (pdf2image, poppler_path), ConvertError;
  - `src/resources/__init__.py` — get_resource_path (pictures/).
  Внешнее: `build/windows/external/poppler-25.07.0/` — бинарники poppler для Windows
  (poppler_path в settings.json); `settings_example.json` → settings.json с токеном;
  `start.bat`; `.vscode/launch.json`. Тесты: tests/test_config.py, test_converter.py.
- **§6 Правила проекта** — репозиторий публичный: никаких токенов, реальных данных клиентов
  и внутренних URL в коде, доках и фикстурах; токен только в gitignored settings.json
  (пример — settings_example.json с заглушкой).
- **§7 Версионирование** — версия в pyproject.toml; релиз — тег vX.Y.Z (текущий: v0.1.0).
- **§8 Тестирование и проверка** — после изменения кода, строго по порядку:
  1) `pytest`; 2) `ruff check .`. При изменении mainwindow.ui сначала регенерировать
  `gui/ui/` (`python src/gui/__build__.py`). В CI те же шаги на Python 3.12–3.14 (ветка master).
- **§9 Эскалация** — перенести как есть из moy_sklad §9 (команды локально, не объединять
  разнородные команды в одном вызове, при отказе предложить выполнить самому).
- **§10 Делегирование субагентам** — перенести как есть из moy_sklad §10 (атомарные срезы,
  запрет анализа домена, готовый контракт и точные пути, скоуп «только эти файлы», краткий
  отчёт, сначала фиксация фактов, частые фактологические вопросы — субагенту `researcher`).

### 3. `README.md` (ru)

Разделы:
- Назначение: PyQt5-приложение для печати этикеток из МойСклада (ассортимент, кастомные
  шаблоны, PDF→JPEG через poppler, печать на термопринтере).
- Требования: Python >=3.12; poppler для Windows — в `build/windows/external/poppler-25.07.0`
  (путь задаётся в settings.json).
- Установка: venv + `pip install -e ".[dev]"`; генерация UI: `python src/gui/__build__.py`.
- Конфигурация: скопировать settings_example.json → settings.json, заполнить
  moy_sklad_token и poppler_path (settings.json в gitignore).
- Запуск: `start.bat` или `python src/PrintLabelMS/__main__.py settings.json`.
- Проверка: `pytest`, `ruff check .`; CI на Python 3.12–3.14.

### 4. `.vscode/settings.json`

Копия из moy_sklad:

```json
{
    "python.testing.pytestArgs": [
        "tests"
    ],
    "python.testing.unittestEnabled": false,
    "python.testing.pytestEnabled": true
}
```

### 5. `tests/test_config.py`

- read_config(settings_example.json) (путь — относительно корня репо через
  `Path(__file__).parent.parent`): валидация модели Config;
- проверки по фактическим полям: printer.name == "TSC TE200", printer.resolution == 600,
  len(label_formats) == 2, orientation из Orientation.

### 6. `tests/test_converter.py`

- Deterministic-тест без poppler в системе: Converter(poppler_path=<пустой tmp_path>) →
  convert_pdf_to_jpeg(b"%PDF-1.4 fake", 200) бросает ConvertError (pdfinfo не найден
  в указанном каталоге).
- Тесты GUI-модули не импортируют (в CI нет дисплея).

### 7. `.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches: [master]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.12", "3.13", "3.14"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install
        run: pip install -e ".[dev]"
      - name: Ruff
        run: ruff check .
      - name: Pytest
        run: pytest
```

Отличие от moy_sklad: триггер по ветке `master` (дефолтная ветка PrintLabelMS).

### 8. `docs/architecture.md`

Первая документация по факту текущего состояния (по конвенции §3): назначение приложения,
поток данных (settings.json → MSApi: ассортимент/шаблоны/организация → MainWindow →
product.request_label PDF → Converter JPEG → PrintHandler → принтер), ключевые классы и
файлы, точки входа правил. Без исторических оговорок.

## Файлы для модификации

### 1. `.gitignore` (объединённый)

```
__pycache__/
*.py[cod]
*.egg-info/
dist/
.venv/
venv/
.pytest_cache/
.ruff_cache/
.mypy_cache/
.idea/
.env
data
snm_build
.build
ui
rc
settings.json
```

Без `build/` и `.vscode/`: poppler под build/windows/external/ остаётся отслеживаемым
(рантайм-зависимость), .vscode/launch.json тоже. Из moy_sklad взяты: *.py[cod],
*.egg-info/, dist/, .venv/, кэши pytest/ruff/mypy, .env; сохранены прежние: data,
snm_build, .build, ui, rc, settings.json.

### 2. `src/config/__init__.py` (ruff)

- UP042/UP035: `class Orientation(str, Enum)` → `class Orientation(StrEnum)`
  (enum.StrEnum, легально при >=3.12);
- UP006: `List[LabelFormat]` → `list[LabelFormat]`;
- UP045: `Optional[str]` → `str | None`;
- UP015: open(file_path, "r", encoding="utf-8") → open(file_path, encoding="utf-8");
- удалить импорт typing.

### 3. `src/PrintLabelMS/__main__.py` (ruff)

- F401: удалить неиспользуемый `import resources` (splash_screen импортирует его сам).

### 4. `src/gui/MainWindow.py` (ruff)

- F401: удалить неиспользуемый `from MSApi.MSApi import MSApiException`
  (ловится в __main__.py).

### 5. `src/gui/__build__.py` (ruff)

- F811: удалить мёртвое первое определение generate_ui (subprocess/pyuic5), оставить
  второе (PyQt5.uic.compiler).

### 6. `start.bat`

Портативно, без хардкода E:\; python из корневого .venv:

```bat
@echo off
set PLMS_ROOT=%~dp0
"%PLMS_ROOT%.venv\Scripts\python.exe" "%PLMS_ROOT%src\PrintLabelMS\__main__.py" "%PLMS_ROOT%settings.json"
```

## Файлы для удаления

- `requirements.txt` (зависимости переехали в pyproject.toml);
- `.env` (PYTHONPATH=src больше не нужен — импорты даёт editable-установка);
- untrack venvs: `git rm -r --cached build/windows/.venv PrintLabelMS/build/windows/.venv`
  (~4000 файлов; на диске остаются).

## Git

5 коммитов на `master`, порядок:

1. `.gitignore` + untrack venvs + `start.bat`;
2. `pyproject.toml` + `README.md`; удаление `requirements.txt`, `.env`;
3. правки кода под ruff (config, __main__, MainWindow, __build__);
4. `AGENTS.md` + `docs/architecture.md` + этот план (`docs/plans/20261120_printlabelms_env_migration_from_moy_sklad.md`);
5. `tests/` + `.github/workflows/ci.yml` + `.vscode/settings.json`.

## Не входит (явные границы)

- Переписывание/рефакторинг кода приложения сверх ruff-правок;
- LICENSE (Q11: без license-поля);
- Перенос самого пакета moy_sklad и замена MSApi на новый клиент moy_sklad;
- Удаление poppler из git или перенос в LFS/внешний источник;
- Создание тега v0.1.0 (релиз — отдельный шаг);
- Изменения `.vscode/launch.json` (работает без изменений при editable-установке).

## Проверка после реализации

1. Все файлы созданы/изменены по списку выше, содержимое соответствует этому плану.
2. `git status`: venvs не отслеживаются; poppler и .vscode/launch.json — отслеживаются.
3. Создан `.venv` на Python 3.13: `py -3.13 -m venv .venv`,
   `.venv\Scripts\pip install -e ".[dev]"`.
4. Multi-package editable работает:
   `.venv\Scripts\python -c "import gui, config, moy_sklad, activity, resources, pdf_to_image_converter; import PrintLabelMS"`.
5. Сгенерирован UI: `python src/gui/__build__.py` (появилась gui/ui/mainwindow_ui.py).
6. `pytest` — зелёный; `ruff check .` — чисто
   (venv на диске пропускается ruff через .gitignore `.venv/`).
7. Импорт GUI без дисплея: QT_QPA_PLATFORM=offscreen,
   `.venv\Scripts\python -c "import gui.MainWindow"`.
8. Запуск приложения вручную пользователем (start.bat с settings.json) — по желанию.

## Риски

- Диск C: почти полон (~20 КБ свободно): pip-кэш и хранилище выводов инструментов могут
  падать; перед реализацией освободить место на C:.
- Multi-package editable hatchling: проверяется шагом 4 «Проверка»; если не сработает —
  вернуться к пользователю с вопросом, без тихой замены решения.
- MSApi (sdist от 2023) на Python 3.14: покажет CI; при поломке сузить матрицу до
  3.12–3.13 и поправить §8 AGENTS.md/CI.
