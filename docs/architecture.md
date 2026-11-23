# Архитектура PrintLabelMS

## Назначение

PrintLabelMS — PyQt5-приложение для печати этикеток из МойСклада. Пользователь
выбирает товары, формат и шаблон этикетки; приложение запрашивает PDF-этикетку
у МойСклада, конвертирует её в JPEG и печатает на термопринтере.

## Поток данных

1. `settings.json` читается в pydantic-модель `Config`: токен МойСклада,
   принтер (имя, разрешение), форматы этикеток (размер, смещения, ориентация),
   `check_updates`. Путь — необязательный аргумент CLI, по умолчанию
   `~/.config/printlabelms/settings.json`. Конфиг несёт `schema_version`;
   при изменении схемы применяются миграции (`src/config/migrations.py`),
   файл перезаписывается с бэкапом `settings.json.bak-<timestamp>`;
   версия новее поддерживаемой — понятная ошибка.
2. Токен передаётся в `MoySkladManager`; через него загружаются ассортимент
   (`get_assortment`), кастомные шаблоны (`get_custom_templates`)
   и организации (`get_organizations`, используется первая).
3. `MainWindow` показывает список товаров с фильтром, выбор формата этикетки
   и шаблона; по кнопке печати в фоновом потоке:
   - `manager.request_label(product, organization, template)` — PDF-этикетка
      от МойСклада;
   - `Converter.convert_pdf_to_jpeg(pdf_data, resolution)` — JPEG через pypdfium2
     (масштаб = resolution / 72);
   - `PrintHandler.print_pdf(jpeg_data)` — QPixmap → QPrinter: размер страницы
     по выбранному формату, ориентация, смещения (мм → пиксели по разрешению),
     число копий.
4. Ошибки МойСклада/сети/конвертации показываются диалогами (`message_box`,
   `QMessageBox`); прогресс — `QProgressDialog`.

## Обновление и откат

Приложение устанавливается в домашний каталог (install.sh): версии живут в
`~/.local/share/printlabelms/versions/<X.Y.Z>/venv`, активная версия — симлинк
`current`, предыдущая — `previous`; хранятся две версии. Приложение считается
установленным, если существует симлинк `current`; при запуске из репозитория
(dev-режим) команды обновления недоступны, а уведомление в GUI не показывается.

Установщик создаёт launcher `~/.local/bin/printlabelms` — симлинк на
`current/venv/bin/printlabelms`; если `~/.local/bin` отсутствует в PATH,
каталог добавляется в `~/.bashrc`. `.desktop`-файл с иконкой создаётся
дважды: запись в меню (`~/.local/share/applications`) и ярлык на рабочем
столе (каталог — `xdg-user-dir DESKTOP`).

Поток обновления (`src/updater/installer.py`):
1. Активный конфиг сохраняется снимком в каталог заменяемой версии
   (`versions/<старая>/settings.json`) — его вернёт откат.
2. Wheel и `SHA256SUMS` скачиваются из GitHub Releases, SHA256 проверяется.
3. Создаётся venv во временном каталоге, `pip install --upgrade <wheel>`.
4. Health-check: `printlabelms --version` и импорт GUI при
   `QT_QPA_PLATFORM=offscreen`; при провале временный каталог удаляется,
   активная версия не трогается.
5. Каталог переименовывается в `versions/<X.Y.Z>`, симлинки переключаются
   (старая версия становится `previous`), более старые версии удаляются.
6. В лог (`~/.local/state/printlabelms/update.log`) пишутся версии и
   `pip freeze`.

Откат (`rollback`): текущий конфиг сохраняется как
`settings.json.bak-rollback-<timestamp>`, снимок конфига предыдущей версии
восстанавливается в `~/.config/printlabelms/settings.json` (нет снимка —
предупреждение, конфиг не трогается), симлинк `current` переключается на
`previous` с health-check; при провале прежние `current` и конфиг возвращаются.

Проверку новой версии и выполнение update/rollback ведёт сервис
`UpdateService` (`src/gui/update_service.py`): фоновая проверка раз в 24 ч
(кэш `~/.cache/printlabelms/update_check.json`, флаг `check_updates`)
эмитит доступную версию, update/rollback выполняется в отдельном потоке
с сигналами прогресса и результата. GUI (статус-бар + кнопка «Обновить»)
показывает уведомление; после успешного обновления приложение
перезапускается.

## Ключевые классы и файлы

- `src/config/__init__.py` — модели `Config`, `PrinterConfig`, `LabelFormat`,
  `Orientation`; `read_config(file_path)`.
- `src/config/migrations.py` — `CURRENT_SCHEMA_VERSION`, `MIGRATIONS`, `migrate(raw)`;
- `src/PrintLabelMS/__main__.py` — точка входа: сборка приложения, загрузка данных
  МойСклада, запуск окна.
- `src/PrintLabelMS/print_handler.py` — `init_printer`, `get_qt_orientation`,
  `PrintHandler`; контракт печати: PDF → JPEG → QPixmap → QPrinter.
- `src/updater/paths.py` — XDG-пути установки (versions/current/previous,
  конфиг, лог, кэш).
- `src/updater/release.py` — GitHub Releases: `fetch_latest_release`,
  `fetch_release_by_tag`, `compare_versions`, выбор ассетов.
- `src/updater/installer.py` — `update(target_version=None, check_only=False)`,
  `rollback`; снимок конфига, SHA256, health-check, переключение симлинков,
  ротация двух версий; ошибки — `UpdaterError`.
- `src/gui/MainWindow.py` — окно приложения; печать выполняется в отдельном
  потоке, результат и ошибки возвращаются в GUI через сигналы.
- `src/gui/update_service.py` — `UpdateService`: фоновая проверка новой
  версии (кэш 24 ч) и выполнение update/rollback в отдельном потоке;
  общается с GUI через сигналы (`update_available`, `progress_changed`,
  `finished`).
- `src/moysklad_manager/models.py` — `Assortment` (наследует библиотечный
  `MoySkladAssortment`, добавляет `salePrices` для export), `LabelTemplate`
  (кастомный шаблон этикетки).
- `src/moysklad_manager/getters.py` — `get_assortment`,
  `get_custom_templates`: обход эндпоинтов через библиотечный
  `walk_for_href`.
- `src/moysklad_manager/manager.py` — `MoySkladManager(token)`: ассортимент,
    кастомные шаблоны, организации (библиотечный `MoySkladOrganization`),
    `request_label(product, organization, template)`; адаптер над внешней
    библиотекой moy_sklad (`MoySkladClient`).
- `src/moysklad_manager/exceptions.py` — `MoySkladError`.
- `src/pdf_to_image_converter/converter.py` — `Converter.convert_pdf_to_jpeg` (pypdfium2), `ConvertError`.
- `src/gui/__build__.py` — генерация `gui/ui/*_ui.py` из `.ui`-форм
  (`mainwindow.ui`); папка `gui/ui/` не коммитится.
- `src/resources/__init__.py` — пути к ресурсам (pictures/).

## Точки входа правил

- Контракт данных: `settings_example.json` → модель `Config`; токен только в
  gitignored `settings.json`.
- Печать: размер страницы и смещения задаются выбранным форматом этикетки;
  разрешение — из `PrinterConfig.resolution`.
- Валидация конфигурации: размеры форматов > 0, смещения >= 0, разрешение
  принтера > 0 (pydantic-валидация моделей в `src/config/__init__.py`).
- Миграции конфига: цепочка по `schema_version` (отсутствие = 1); при
  изменении схемы — бэкап и атомарная перезапись; версия новее
  поддерживаемой — отказ.
- Обновление: SHA256 wheel проверяется до установки; health-check обязателен
  перед переключением `current`; снимок конфига в каталоге версии — основа
  отката.
- Ошибки: фатальные (запуск) — через `gui.message_box.fatal_error`;
  операционные (печать) — диалог в окне.
