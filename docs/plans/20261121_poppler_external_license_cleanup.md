# План: poppler вне git (скрипты загрузки), MIT-лицензия, очистка, починка -m режима

Источник: решения пользователя по находкам ревью
(отчёт `C:\Users\nsr\.opencode\plan\printlabelms_full_review_20261120.md`)
и списку «Осталось за тобой» от 2026-11-20.

## Решения (согласовано с пользователем, 2026-11-21)

| Вопрос | Решение |
| --- | --- |
| M7. Poppler в git (~450 файлов) | Убрать из git (`git rm --cached`, на диске остаётся); два скрипта загрузки: Windows — zip с GitHub Releases этого репозитория (URL параметризуется), Linux — пакетный менеджер; `build/windows/external/` в gitignore |
| M8. LICENSE | MIT (файл LICENSE + license-поле в pyproject.toml) |
| M9. Тег v0.1.0 и origin/develop | Ветку develop удалить сейчас; тег пока не создавать → TODO.md |
| M3. Проверка размера PDF vs формат этикетки | Не реализовывать, записать в TODO.md |
| L1/L6/L7 | Удалить пакет `src/activity` (+ packages в pyproject), убрать `build/linux/*`, удалить старые venv на диске (`build/windows/.venv`, `PrintLabelMS/build/windows/.venv`) |
| Сломанный режим `python -m PrintLabelMS` | Починить: импорт print_handler через полное имя `PrintLabelMS.print_handler` (работает и в скриптовом режиме, и в -m) |

## Файлы для создания

- `scripts/download_poppler_windows.bat` — скачивает zip с GitHub Releases
  (URL в начале файла, по умолчанию
  `https://github.com/gusya1/PrintLabelMS/releases/download/poppler-windows-x64-25.07.0/poppler-windows-x64-25.07.0.zip`),
  распаковывает в `build/windows/external/`, проверяет наличие
  `poppler-25.07.0/Library/bin/pdfinfo.exe`; архив должен содержать папку
  `poppler-25.07.0/` на верхнем уровне;
- `scripts/download_poppler_linux.sh` — установка poppler-utils (+poppler-data)
  через apt-get/dnf, вывод инструкции по poppler_path в settings.json
  (null или /usr/bin);
- `LICENSE` — MIT, copyright gusya1;
- `TODO.md` — тег v0.1.0 и M3 (проверка размера PDF).

## Файлы для модификации

- `.gitignore`: добавить `build/windows/external/`;
- `pyproject.toml`: убрать `src/activity` из packages; добавить
  `license = {text = "MIT"}`;
- `README.md`: poppler ставится скриптами (Требования + Установка);
- `AGENTS.md`: §5 — external poppler скачивается скриптом, убрать пункты
  activity и build/linux из карты проекта;
- `src/PrintLabelMS/__main__.py`:
  `from print_handler import PrintHandler` →
  `from PrintLabelMS.print_handler import PrintHandler`.

## Файлы для удаления

- `git rm -r --cached build/windows/external/poppler-25.07.0` (на диске остаётся);
- `git rm -r src/activity`, `git rm -r build/linux`;
- с диска: `build/windows/.venv`, `PrintLabelMS/build/windows/.venv`
  и опустевший каталог `PrintLabelMS/`.

## Git

- Удалить удалённую ветку: `git push origin --delete develop`.
- Коммиты — тематические, на master (по решению пользователя).

## Срезы (по одному субагенту за раз)

1. M7: poppler из git + скрипты + .gitignore + README + AGENTS.md;
2. M8: LICENSE + license-поле pyproject (+ проверка сборки wheel);
3. L1/L6/L7: activity, build/linux, venv на диске + карта проекта в AGENTS.md;
4. Починка -m режима (__main__.py) + проверка обоих режимов запуска;
5. TODO.md + удаление origin/develop.

## Проверка

После каждого среза: 1) `pytest`; 2) `ruff check .` (для срезов без кода —
`git status`). Срез 4 дополнительно: оба режима запуска без аргументов
(offscreen) → usage-сообщение, exit 1. После всех срезов — оффскрин-импорт GUI.

## Актуализация документации

README.md (poppler через скрипты), AGENTS.md (§5 карта проекта и external
poppler) — в рамках срезов 1 и 3; docs/architecture.md не меняется
(поток данных не затрагивается).
