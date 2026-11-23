# AGENTS.md - Project Notes for AI Agents

## 1. Обзор проекта

PrintLabelMS — самостоятельное PyQt5-приложение для печати этикеток из МойСклада:
загрузка ассортимента, кастомных шаблонов этикеток и организации через библиотеку moy_sklad;
PDF-этикетка конвертируется в JPEG (pypdfium2 + Pillow) и печатается на термопринтере.

### Стек
- Python >= 3.12
- PyQt5>=5.15.6, moy_sklad @ git+https://github.com/gusya1/moy_sklad@v0.1.0,
  pydantic>=2.11, requests>=2.32, pypdfium2>=5.15, Pillow>=13
- Сборка: hatchling (editable-установка); тесты: pytest; линт: ruff (line-length 121)

## 2. Окружение
- Локальный venv `.venv` + `pip install -e ".[dev]"`.
- Перед запуском GUI сгенерировать UI из форм: `python src/gui/__build__.py`
  (папка `gui/ui/` в gitignore).
- Токен МойСклада хранится только в settings.json (gitignored), не в коде, git и фикстурах.
- Версия приложения 0.4.0; релиз — тег vX.Y.Z (CI публикует GitHub Release).

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
- `src/PrintLabelMS/__main__.py` — точка входа: main(), argparse, --version, подкоманды update/rollback,
  запуск GUI с ленивым импортом Qt;
- `src/PrintLabelMS/print_handler.py` — `init_printer`, `get_qt_orientation`,
  `PrintHandler` (размер/ориентация/смещения/копии, print_pdf: JPEG → QPixmap → QPrinter);
- `src/config/__init__.py` — pydantic-модели Config/PrinterConfig/LabelFormat/Orientation
  и read_config (settings.json);
- `src/config/migrations.py` — CURRENT_SCHEMA_VERSION и MIGRATIONS (N → N+1), migrate(raw);
- `src/gui/MainWindow.py` — окно: список товаров с фильтром, выбор формата этикетки и
  шаблона, печать в фоне (threading + QProgressDialog), диалоги ошибок;
- `src/gui/update_service.py` — UpdateService: фоновая проверка новой версии
  (кэш 24 ч), текущая версия активной установки, update/rollback в отдельном
  потоке, общается с GUI через сигналы (update_available, progress_changed, finished);
- `src/gui/splash_screen.py`, `src/gui/message_box.py` — сплэш и фатальные ошибки;
- `src/gui/__build__.py` — генерация `gui/ui/*_ui.py` из `.ui`-форм (PyQt5.uic);
  `mainwindow.ui` — исходная форма;
- `src/moysklad_manager/__init__.py` — пустой пакет (без реэкспортов),
  импорты из подмодулей;
- `src/moysklad_manager/models.py` — Assortment (наследует библиотечный
  MoySkladAssortment, добавляет salePrices для export) и LabelTemplate
  (кастомный шаблон этикетки);
- `src/moysklad_manager/getters.py` — get_assortment, get_custom_templates:
  обход через библиотечный walk_for_href по entity/assortment и
  entity/assortment/metadata/customtemplate;
- `src/moysklad_manager/manager.py` — адаптер над внешней библиотекой moy_sklad
  (MoySkladClient): MoySkladManager(token) с get_assortment,
  get_custom_templates, get_organizations (библиотечный MoySkladOrganization),
  request_label(product, organization, template);
- `src/updater/paths.py` — XDG-пути установки (versions/current/previous, конфиг, лог, кэш);
- `src/updater/release.py` — GitHub Releases (latest / по тегу), сравнение версий, выбор ассетов;
- `src/updater/installer.py` — update/rollback: снимок конфига, SHA256, venv в каталоге
  версии (без tmp-переименования), health-check, переключение симлинков, ротация двух версий, лог;
- `src/moysklad_manager/exceptions.py` — MoySkladError;
- `src/pdf_to_image_converter/converter.py` — Converter.convert_pdf_to_jpeg
  (pypdfium2, scale = resolution / 72), ConvertError;
- `src/resources/__init__.py` — get_resource_path (pictures/).
`settings_example.json` → settings.json с токеном;
`start.bat`; `.vscode/launch.json`.
- `scripts/install.sh` — бутстрап установки на Linux без sudo (preflight, wheel+SHA256SUMS из GitHub Releases, venv, health-check, симлинки, конфиг-шаблон, launcher + PATH в ~/.bashrc, .desktop: меню и рабочий стол); флаги --version X.Y.Z, --force;
Тесты: tests/test_build.py, test_config.py, test_config_migrations.py, test_cli.py, test_converter.py, test_moysklad_manager.py, test_update_service.py, test_updater.py.

## 6. Правила проекта
- Репозиторий публичный: никаких токенов, реальных данных клиентов и внутренних URL в коде, доках и фикстурах; токен только в gitignored settings.json (пример — settings_example.json с заглушкой).

## 7. Версионирование
- Версия в pyproject.toml; релиз — тег vX.Y.Z (текущий: v0.4.0): CI по тегу публикует GitHub Release с wheel, install.sh и SHA256SUMS.

## 8. Тестирование и проверка
После изменения кода, строго по порядку:
1) `pytest`;
2) `ruff check .`.
При изменении mainwindow.ui сначала регенерировать `gui/ui/` (`python src/gui/__build__.py`).
В CI те же шаги + сборка wheel со smoke-тестом в чистом venv (Python 3.14) на Python 3.12–3.14 (ветка master); по тегу vX.Y.Z — job публикации GitHub Release.

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
