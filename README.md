# PrintLabelMS

## Назначение

PyQt5-приложение для печати этикеток из МойСклада: загрузка ассортимента, кастомных
шаблонов этикеток и организации через библиотеку moy_sklad; PDF-этикетка конвертируется
в JPEG (pypdfium2 + Pillow) и печатается на термопринтере.

## Требования

- Python >= 3.12
- Linux (установка через install.sh): `python3` (>= 3.12), `git`, `curl`;
  для создания venv может потребоваться пакет `python3-venv`
- Внешние бинарники не нужны: конвертация PDF выполняется pypdfium2

## Установка на Linux

Одна команда — скачивает и запускает установщик из последнего GitHub Release
(без sudo, установка в домашний каталог):

```bash
curl -fsSLO https://github.com/gusya1/PrintLabelMS/releases/latest/download/install.sh && bash install.sh
```

Установщик:
- проверяет `python3` (>= 3.12), `git`, `curl`;
- скачивает wheel и `SHA256SUMS` из GitHub Releases, проверяет SHA256;
- создаёт изолированный venv в `~/.local/share/printlabelms/versions/<X.Y.Z>/venv`
  и переключает симлинк `current`;
- создаёт шаблон конфига `~/.config/printlabelms/settings.json` (если его нет);
- создаёт launcher `~/.local/bin/printlabelms` (при отсутствии каталога в PATH
  добавляет его в `~/.bashrc`) и `.desktop` с иконкой: запись в меню
  приложения и ярлык на рабочем столе.

Перед первым запуском вставьте токен МойСклада в
`~/.config/printlabelms/settings.json`.

Опции: `--version X.Y.Z` (конкретная версия), `--force` (переустановить).
Если приложение уже установлено, повторный запуск install.sh делегирует
обновление команде `printlabelms update`.

## Обновление и откат

- `printlabelms update` — обновление до последнего релиза;
  `printlabelms update --to X.Y.Z` — конкретная версия;
  `printlabelms update --check` — только проверка наличия новой версии.
- GUI показывает новую версию в статус-баре (проверка при каждом старте,
  если включено `check_updates`) и даёт кнопку «Обновить»: обновление
  в отдельном потоке, после установки приложение просит его перезапустить
  (само не перезапускается).
- `printlabelms rollback` — откат к предыдущей версии (хранятся две) с
  восстановлением снимка конфига той версии.

## Конфигурация

Конфиг — `~/.config/printlabelms/settings.json` (создаётся установщиком;
пример — `settings_example.json`). Поля: `schema_version`, `moy_sklad_token`,
`check_updates`, `printer` (имя, разрешение), `label_formats`. Токен хранится
только в gitignored-файле `settings.json`.

## Установка из репозитория (разработка)

```bat
py -3.13 -m venv .venv
.venv\Scripts\pip install -e ".[dev]"
python src/gui/__build__.py
start.bat
```

Генерация UI (`python src/gui/__build__.py`) создаёт `src/gui/ui/*_ui.py` из `.ui`-форм
(папка `gui/ui/` в gitignore). Запуск: `printlabelms [settings.json] [--kiosk]`;
`--kiosk` открывает окно во весь экран, `F11` переключает полноэкранный и оконный режим
в любом запуске.
Команды обновления и уведомление о новой версии доступны только для
установленного через install.sh приложения.

## Проверка

- `pytest`
- `ruff check .`
- CI на Python 3.12–3.14 (ветка master): тесты, сборка wheel и smoke-тест;
  тег `vX.Y.Z` — публикация GitHub Release (wheel, `install.sh`, `SHA256SUMS`)
