# План: исправление находок полного ревью (2026-11-20)

Источник: отчёт ревью `C:\Users\nsr\.opencode\plan\printlabelms_full_review_20261120.md`
(находки C1–C5, M1–M9, L1–L11). Реализация — субагентами по одному за раз,
атомарные срезы «модуль + тест», скоуп «только эти файлы».

## Решения (согласовано с пользователем)

| Вопрос | Решение |
| --- | --- |
| C3. `__build__.py` падает на чистом клоне | Создавать `gui/ui/` перед генерацией; файл вывода — через `with`; тест в tmp_path |
| C1. Thread-safety печати | Снапшот UI-состояния (товар, формат, шаблон, количество) в GUI-потоке до старта воркера; воркер не трогает `self.ui` |
| C4. N+1 API-вызовы при старте | Имя товара брать из `meta.name` без полного GET (`product.get_json()['meta']['name']`) |
| C2. Тихий сбой печати | Проверка `painter.begin()` и `pixmap.isNull()` → RuntimeError; удалить мёртвую константу `poppler_path` в print_handler.py |
| C5 + M1. __main__.py | Сначала проверка пустого списка организаций, затем `[0]`; ловить OSError/ValidationError через fatal_error |
| M2. Конвертер | Ловить все 4 исключения pdf2image → ConvertError; тесты monkeypatch'ем convert_from_bytes (без poppler в CI) |
| M4. Адаптер moy_sklad | `get_assortment` — `list(Assortment.gen_list())`; тест с monkeypatch gen_list |
| M6. .gitignore | Убрать голые паттерны `ui`, `data`, `snm_build`, `.build`, `rc`; добавить якорный `src/gui/ui/` |
| L1/L3/L4/L5/L10. Мелкие правки | config: валидация полей + `with open`; MainWindow: русские строки UI, «Готово» только при успехе, диалоги с родителем, понятная ошибка пустого формата; иконку окна — из icon.png |
| GUI-тесты в CI | Не добавлять (нет дисплея) — ограничение плана миграции сохраняется; проверка GUI — оффскрин-импорт локально |

## Не входит (решения пользователя, отдельно)

- M3. Строгая проверка соответствия размера PDF формату этикетки
  (может сломать рабочие настройки шаблонов МойСклада — нужен выбор:
  ошибка/предупреждение/без проверки);
- M7. Poppler в git (~450 файлов): LFS / внешний download / оставить;
- M8. LICENSE для публичного репозитория;
- M9. Тег v0.1.0 и судьба ветки origin/develop;
- L1 (частично). Удаление пакета `activity` (заглушка, не используется) —
  затрагивает packages в pyproject.toml;
- L6/L7. build/linux/* и старые venv на диске.

## Срезы (по одному субагенту за раз)

1. `src/gui/__build__.py` + `tests/test_build.py` (C3).
2. `src/config/__init__.py` + `tests/test_config.py` (L10, L2).
3. `src/PrintLabelMS/print_handler.py` (C2, L1) — без GUI-теста.
4. `src/gui/mainwindow.ui` → регенерация `gui/ui/` + `src/gui/MainWindow.py`
   (C1, C4, L3, L4, L5, иконка).
5. `src/PrintLabelMS/__main__.py` (C5, M1) — без GUI-теста.
6. `src/pdf_to_image_converter/converter.py` + `tests/test_converter.py` (M2).
7. `src/moy_sklad/__init__.py` + тест (M4).
8. `.gitignore` (M6).
9. Актуализация документации: AGENTS.md, docs/architecture.md.

## Проверка после каждого среза

1) `pytest`; 2) `ruff check .`. Для среза 4 — сначала
`python src/gui/__build__.py`. После всех срезов — оффскрин-проверка импорта
GUI и итоговый отчёт пользователю с перечнем нерешённых пунктов.
