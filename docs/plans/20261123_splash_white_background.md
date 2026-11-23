# План: белый непрозрачный фон сплэш-экрана (TODO пункт 2)

Источник: TODO.md, пункт 2 — «На линукс png splash screen делает черный
фон. Нужно белый. Если это нельзя регулировать, нужно переделать splash
screen на jpeg».

## Проблема

`src/gui/splash_screen.py` создаёт `QSplashScreen` из `snm_logo.png`.
PNG — RGBA (327×298, ~75% пикселей прозрачные). В qtbase 5.15
`QSplashScreenPrivate::setPixmap()` ставит
`WA_TranslucentBackground`, если pixmap имеет альфу
(`setAttribute(Qt::WA_TranslucentBackground, pixmap.hasAlpha())`).
На Linux без композитинга прозрачные области такого окна рендерятся
чёрным — пользователь видит чёрный фон вместо белого.

Регулирование возможно: opaque-пixmap с белым фоном не имеет альфы →
атрибут translucency не ставится → окно непрозрачное на всех
платформах. JPEG (fallback из TODO) не нужен, PNG остаётся исходником
ассета.

## Факты по Qt 5 (qtbase v5.15.2, проверено по исходникам)

- `showMessage(message, alignment=Qt::AlignLeft, color=Qt::black)` —
  цвет текста по умолчанию чёрный; на белом фоне статус
  «Загружаем товары...» остаётся видимым, наследование
  `QSplashScreen` не требуется.
- Геттеры `pixmap()` и `message()` существуют (для теста).

## Файлы для модификации

- `src/gui/splash_screen.py`: логотип композитируется на белый фон —
  `QImage(logo.size(), Format_RGB32)` + fill white + QPainter.drawImage;
  `QSplashScreen` создаётся из `QPixmap.fromImage(image)`.
  `Format_RGB32` гарантирует отсутствие альфа-канала.
  `showMessage("Загружаем товары...")` — без изменений.
  `src/PrintLabelMS/__main__.py` не меняется.
- `docs/architecture.md`: из «Ключевые классы и файлы» убрать строки
  про `MainWindow.py` и `update_service.py` (GUI описан отдельно),
  добавить указание на `docs/gui.md`.

## Файлы для создания

- `tests/test_splash_screen.py`: offscreen-QApplication фикстура
  (`QT_QPA_PLATFORM=offscreen`, модульный скоуп); проверки:
  - `splash.pixmap().toImage()` без альфа-канала
    (`hasAlphaChannel() == False`) — контракт против чёрного фона;
  - четыре угла pixmap'а белые (у исходного PNG углы прозрачные,
    alpha=0 — проверено);
  - `splash.message() == "Загружаем товары..."`.
  Файл идёт алфавитно перед `test_update_service.py`: QApplication
  создаётся первым и переиспользуется его фикстурой
  (`QCoreApplication.instance()`).
- `docs/gui.md` — описание GUI отдельно от architecture.md:
  компоненты (MainWindow, splash_screen, message_box, update_service),
  контракты; для сплэша — правило непрозрачного белого фона и причина
  (Linux без композитинга).

## Проверка

1) `pytest`; 2) `ruff check .`.

## Актуализация документации

`docs/gui.md` (новый), `docs/architecture.md` (GUI вынесен отдельно,
указание на gui.md).
