# План: печать калибровочного прямоугольника по F9

Согласовано с пользователем: горячая клавиша `F9` без кнопок и меню;
эталон — рамка текущего размера ценника с двумя диагоналями; всегда
одна копия; печать в фоновом потоке с прогрессом, как у обычной
печати; рисование напрямую `QPainter` на `QPrinter`.

## Факты

- Размер ценника выбирается в `comboLabelSize` (`LabelFormat`:
  width/height/width_offset/height_offset/orientation, мм), данные
  хранятся в `itemData` комбобокса.
- `PrintHandler` уже умеет задавать размер страницы, ориентацию,
  смещения и число копий (`set_page_size`, `set_orientation`,
  `set_width_offset`, `set_height_offset`, `set_copy_count`);
  `reset_print_settings(label_format, count)` в `MainWindow` применяет
  их одним вызовом.
- `MainWindow` печатает в отдельном потоке (`threading.Thread`) под
  `QProgressDialog`, результат/ошибки — через сигналы
  `progress_changed` / `error_expected`; флаг `__printing` запрещает
  обновление во время печати.
- В `mainwindow.ui` нет меню и `QShortcut`; шорткат создаётся в коде
  окна. Форму не трогаем.
- Тесты GUI в репозитории используют offscreen-QApplication
  (`tests/test_ui_scale.py`).

## Файлы для модификации

- `src/PrintLabelMS/print_handler.py`:
  - константа `CALIBRATION_LINE_WIDTH_MM = 0.3`;
  - `draw_calibration(painter, width_px, height_px, line_width_px)` —
    рамка по границам устройства (линия с толщиной `line_width_px`
    укладывается внутрь: отступ `line_width_px // 2`) и две диагонали
    из угла в угол;
  - `PrintHandler.print_calibration(width_mm, height_mm)` —
    `QPainter.begin(self.__printer)`, `translate` на смещения, рисование
    рамки через `mm_to_device_pixels`, `end()` в `finally`; ошибка
    начала печати — `RuntimeError("Не удалось инициализировать принтер
    для печати")`.
- `src/gui/MainWindow.py`:
  - `QShortcut(QKeySequence("F9"), self)` в `__init__`, слот
    `__onCalibrationShortcut`;
  - слот: при `__printing` — предупреждение «Идёт печать»; нет
    выбранного формата — диалог «Формат этикетки не выбран»; иначе
    поток + `QProgressDialog("Калибровка...", None, 0, 2)`, шаги
    «Калибровка...» → «Готово», ошибки через `error_expected`,
    `__printing` взводится на время печати;
  - `__print_calibration(label_format)`:
    `reset_print_settings(label_format, 1)` →
    `print_calibration(label_format.width, label_format.height)`;
  - хелпер `__current_label_format()` (выбор из комбобокса с ошибкой)
    переиспользуется в `__collect_print_params`.
- `tests/test_print_handler.py`: offscreen-фикстура `QGuiApplication`;
  тест `draw_calibration` на `QImage` 100×60 — тёмные пиксели рамки
  (левая/правая/верхняя/нижняя стороны), центр пересечения диагоналей;
  светлые — внутри вне линий и вне рамки.
- `docs/gui.md`: F9 и калибровочный эталон в разделе главного окна.
- `docs/architecture.md`: калибровка в шаге потока данных и в описании
  `PrintHandler`.
- `AGENTS.md`: упоминание `print_calibration` в карте проекта.
- `TODO.md`: пункт 7 со ссылкой на этот план.

## Ограничения

- Версия приложения не меняется.
- Продукт/шаблон/сеть для калибровки не нужны: печатается только
  геометрия текущего формата.
- Копий всегда одна, `spinCount` не влияет.
- Шорткат действует в пределах окна (контекст по умолчанию), не
  глобальный.

## Проверка

1) `pytest`; 2) `ruff check .`. Формы (`mainwindow.ui`) не менялись —
регенерация `gui/ui/` не требуется.

## Актуализация документации

Обновлены `docs/gui.md` и `docs/architecture.md`; новый раздел
документации не требуется.
