# Архитектура PrintLabelMS

## Назначение

PrintLabelMS — PyQt5-приложение для печати этикеток из МойСклада. Пользователь
выбирает товары, формат и шаблон этикетки; приложение запрашивает PDF-этикетку
у МойСклада, конвертирует её в JPEG и печатает на термопринтере.

## Поток данных

1. `settings.json` (путь — аргумент запуска) читается в pydantic-модель `Config`:
   токен МойСклада, путь к poppler, принтер (имя, разрешение), форматы этикеток
   (размер, смещения, ориентация).
2. Токен передаётся в MSApi (`MSApi.set_access_token`); загружаются ассортимент
   (`get_assortment`), кастомные шаблоны (`get_assortment_custom_templates`)
   и организации (`get_organizations`, используется первая).
3. `MainWindow` показывает список товаров с фильтром, выбор формата этикетки
   и шаблона; по кнопке печати в фоновом потоке:
   - `product.request_label(organization, template)` — PDF-этикетка от МойСклада;
   - `Converter.convert_pdf_to_jpeg(pdf_data, resolution)` — JPEG через pdf2image
     (poppler из `poppler_path`);
   - `PrintHandler.print_pdf(jpeg_data)` — QPixmap → QPrinter: размер страницы
     по выбранному формату, ориентация, смещения (мм → пиксели по разрешению),
     число копий.
4. Ошибки МойСклада/сети/конвертации показываются диалогами (`message_box`,
   `QMessageBox`); прогресс — `QProgressDialog`.

## Ключевые классы и файлы

- `src/config/__init__.py` — модели `Config`, `PrinterConfig`, `LabelFormat`,
  `Orientation`; `read_config(file_path)`.
- `src/PrintLabelMS/__main__.py` — точка входа: сборка приложения, загрузка данных
  МойСклада, запуск окна.
- `src/PrintLabelMS/print_handler.py` — `init_printer`, `get_qt_orientation`,
  `PrintHandler`; контракт печати: PDF → JPEG → QPixmap → QPrinter.
- `src/gui/MainWindow.py` — окно приложения; печать выполняется в отдельном
  потоке, результат и ошибки возвращаются в GUI через сигналы.
- `src/moy_sklad/__init__.py` — адаптер над сторонним MSApi: ассортимент,
    кастомные шаблоны, организации (не пакет moy_sklad).
- `src/pdf_to_image_converter/converter.py` — `Converter`, `ConvertError`.
- `src/PrintLabelMS/exceptions.py` — `AppError`, `MoySkladError`.
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
- Ошибки: фатальные (запуск) — через `gui.message_box.fatal_error`;
  операционные (печать) — диалог в окне.
