# План: масштабирование интерфейса — ui_scale в settings.json (TODO пункт 4)

Источник: TODO.md, пункт 4 — «Масштабирование интерфейса». Согласовано:
настройка только в JSON, без горячих клавиш.

## Факты

- Qt 5.15.2 / PyQt5 5.15.11: HiDPI включён по умолчанию с Qt 5.14;
  масштабируемость UI добавляется масштабированием шрифта приложения —
  layout'ы формы без жёстких размеров растягивают все виджеты
  пропорционально (комбо, спинбоксы, кнопки, строки списка).
- Конфиг приходит в `on_loaded` (`StartupLoader`) → масштаб применяется на
  главном потоке до создания `MainWindow`.
- `settings_example.json` читается тестом из репо: при повышении версии
  схемы его обязательно обновить, иначе миграция перезапишет файл и
  создаст бэкап в корне репо.

## Файлы для модификации

- `src/config/__init__.py`: `Config` — `ui_scale: float = Field(default=1.0, gt=0)`.
- `src/config/migrations.py`: `CURRENT_SCHEMA_VERSION` → 3;
  `_migrate_2_to_3`: `raw.setdefault("ui_scale", 1.0)` (конвенция как у
  `check_updates` в v2).
- `src/PrintLabelMS/__main__.py`: в `on_loaded` —
  `gui.ui_scale.apply_ui_scale(app, config_model.ui_scale)` до создания окна;
  ленивый импорт `gui.ui_scale`.
- `settings_example.json`: `"schema_version": 3`, добавить
  `"ui_scale": 1.0`.
- `tests/test_config.py`: дефолт `ui_scale == 1.0`; `<= 0` → ValidationError.
- `tests/test_config_migrations.py`: v2-конфиг без `ui_scale` — после чтения
  `schema_version == 3`, в файле появился `ui_scale: 1.0`; существующие
  ассерты `== 2` обновить на `== 3`.
- `TODO.md`: удалить пункт 4.
- `docs/architecture.md`: шаг 1 «Поток данных» — поле `ui_scale`;
  «Точки входа правил» → валидация: `ui_scale > 0`.
- `docs/gui.md`: коэффициент масштаба UI из конфига применяется при старте
  масштабированием шрифта приложения (`src/gui/ui_scale.py`).

## Файлы для создания

- `src/gui/ui_scale.py`: `apply_ui_scale(app, ui_scale)` — при
  `ui_scale == 1.0` no-op; иначе копия шрифта приложения с
  `setPointSizeF(base * ui_scale)` (fallback на `pixelSize`, если point
  size не задан) и `app.setFont(...)`.
- `tests/test_ui_scale.py`: offscreen-QApplication + фикстура
  восстановления исходного шрифта; тесты: no-op при 1.0, ×2 и ×0.5
  меняют pointSizeF пропорционально.

## Ограничение (принято)

Сплэш во время загрузки остаётся в базовом масштабе: логотип —
фиксированный pixmap, масштабируется только строка статуса; окно
временное.

## Проверка

1) `pytest`; 2) `ruff check .`. Формы не трогаем.

## Актуализация документации

`docs/architecture.md`, `docs/gui.md`, `TODO.md` (удаление пункта 4).
