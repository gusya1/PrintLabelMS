# AGENTS.md - Project Notes for AI Agents

## 1. Обзор проекта

PrintLabelMS — самостоятельное PyQt5-приложение для печати этикеток из МойСклада:
загрузка ассортимента, кастомных шаблонов этикеток и организации через MSApi;
PDF-этикетка конвертируется в JPEG (poppler/pdf2image) и печатается на термопринтере.

### Стек
- Python >= 3.12
- PyQt5>=5.15.6, MSApi==0.2.11, pydantic>=2.11, requests>=2.32, pdf2image>=1.17.0
- Сборка: hatchling (editable-установка); тесты: pytest; линт: ruff (line-length 121)

## 2. Окружение
- Локальный venv `.venv` + `pip install -e ".[dev]"`.
- Перед запуском GUI сгенерировать UI из форм: `python src/gui/__build__.py`
  (папка `gui/ui/` в gitignore).
- Токен МойСклада хранится только в settings.json (gitignored), не в коде, git и фикстурах.
- Версия приложения 0.1.0; релиз по тегу.

## 3. Документация
- Документация проекта находится в docs/.
- Файлы в docs/plans/ не редактируй и не удаляй: это история изменений и планов.
- Перед изучением кода сначала ищи в docs/ информацию о задаче, планы и соглашения.
- Если нужной документации нет, фиксируй находки и напиши документацию по факту.
- Документация (кроме docs/plans/) описывает только фактическое состояние репозитория, без исторических оговорок вида "больше нет", "раньше", "теперь": история хранится в docs/plans/.
- Документация отражает только бизнес-логику и непосредственно связанные с ней общие моменты в коде (контракты данных, точки входа правил); механика реализации (MRO, kwargs, matching, устройство виджетов/JS-событий) в доки не выносится.
- Документация указывает ключевые классы и файлы правил, чтобы было понятно, куда смотреть в коде.

## 4. Планирование
- Новые планы только добавляются новыми файлами: после согласования и до реализации записывай план в docs/plans/<YYYYMMDD>_<formulated plan name>.md.
- Имя файла формулируй по смыслу задачи; дата указывается в формате YYYYMMDD.
- В любой план обязательно включай пункт "Актуализация документации": обнови docs по теме, а если документации по этой теме нет - напиши её.

## 5. Карта проекта
src-layout:
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
Внешнее: poppler для Windows не в git — скачивается
`scripts/download_poppler_windows.bat` в
`build/windows/external/poppler-25.07.0/` (poppler_path в settings.json);
Linux — `scripts/download_poppler_linux.sh`;
`settings_example.json` → settings.json с токеном;
`start.bat`; `.vscode/launch.json`.
Тесты: tests/test_build.py, test_config.py, test_converter.py, test_moy_sklad.py.

## 6. Правила проекта
- Репозиторий публичный: никаких токенов, реальных данных клиентов и внутренних URL в коде, доках и фикстурах; токен только в gitignored settings.json (пример — settings_example.json с заглушкой).

## 7. Версионирование
- Версия в pyproject.toml; релиз — тег vX.Y.Z (текущий: v0.1.0).

## 8. Тестирование и проверка
После изменения кода, строго по порядку:
1) `pytest`;
2) `ruff check .`.
При изменении mainwindow.ui сначала регенерировать `gui/ui/` (`python src/gui/__build__.py`).
В CI те же шаги на Python 3.12–3.14 (ветка master).

## 9. Эскалация
- Команды запускаются локально (pytest, ruff).
- Не объединяй разнородные команды в одном вызове.
- Если отклонено - предложи выполнить самому, не обходи через shell/установку на хост.

## 10. Делегирование субагентам
1. Дроби на атомарные срезы: один модуль плюс тест.
2. Сразу запрещай анализ домена, реализуй только по спецификации.
3. Давай готовый контракт и точные пути.
4. Скоуп: "только эти файлы" и "не трогай".
5. Краткий отчет по пунктам, без рассуждений о домене.
6. Сначала сам зафиксируй факты по коду.
7. Частые фактологические вопросы о сторонних библиотеках, фреймворках, документации и сети — делегируй субагенту `researcher` (инструмент `subagent`), не ищи сам.
