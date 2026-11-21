# PrintLabelMS

## Назначение

PyQt5-приложение для печати этикеток из МойСклада: загрузка ассортимента, кастомных
шаблонов этикеток и организации через MSApi; PDF-этикетка конвертируется в JPEG
(poppler/pdf2image) и печатается на термопринтере.

## Требования

- Python >= 3.12
- poppler:
  - Windows: после клона выполнить `scripts\download_poppler_windows.bat`
    (скачивает zip с GitHub Releases в
    `build/windows/external/poppler-25.07.0`; путь задаётся в settings.json,
    поле `poppler_path`);
  - Linux: выполнить `bash scripts/download_poppler_linux.sh`
    (устанавливает poppler-utils пакетным менеджером; `poppler_path` —
    null или `/usr/bin`).

## Установка

```bat
py -3.13 -m venv .venv
.venv\Scripts\pip install -e ".[dev]"
scripts\download_poppler_windows.bat
python src/gui/__build__.py
```

Генерация UI (`python src/gui/__build__.py`) создаёт `src/gui/ui/*_ui.py` из `.ui`-форм
(папка `gui/ui/` в gitignore).

## Конфигурация

Скопировать `settings_example.json` → `settings.json`, заполнить `moy_sklad_token`
и `poppler_path`. Файл `settings.json` в gitignore — токен не попадает в репозиторий.

## Запуск

```bat
start.bat
```

или:

```bat
python src/PrintLabelMS/__main__.py settings.json
```

## Проверка

- `pytest`
- `ruff check .`
- CI на Python 3.12–3.14 (ветка master)
