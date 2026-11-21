# План: замена MSApi на moy_sklad (пакет moysklad_manager)

Источник: согласованные решения по итогам grilling-сессии 2026-11-21.
Новая библиотека — https://github.com/gusya1/moy_sklad (sync, pydantic v2,
Python >= 3.12, на PyPI не опубликована).

## Решения (согласовано с пользователем, 2026-11-21)

| Вопрос | Решение |
| --- | --- |
| Зависимость | `moy_sklad @ git+https://github.com/gusya1/moy_sklad@<tag>`; ждём тег в git-репозитории. До появления тега в `pyproject.toml` временный пин на commit SHA; мерж — только после тега |
| Локальный пакет | `src/moy_sklad` переименовать в `src/moysklad_manager` (коллизия имени с внешней библиотекой) |
| API адаптера | класс `MoySkladManager(token)`; методы `get_assortment()`, `get_custom_templates()`, `get_organizations()`, `request_label(product, organization, template)` |
| Внешние модели | собственные pydantic-модели; «проводные» куски JSON (`meta`, `salePrices`) хранятся сырыми dict, потому что export требует дословный JSON |
| Ассортимент | эндпоинт `entity/assortment` напрямую через `client.get`, пагинация — библиотечный `walk` |
| Шаблоны | эндпоинт `entity/assortment/metadata/customtemplate` (как в MSApi) |
| Организации | эндпоинт `entity/organization` |
| Недостающее в библиотеке | реализуем в адаптере (ассортимент, шаблоны, export), затем отдельной задачей — PR в библиотеку |
| Экспорт PDF | `client.post("entity/assortment/{id}/export", json.dumps(payload))`; `200` → `response.content`, `303` → `requests.get(Location)` **без** `Authorization`, иначе — ошибка |
| `verify=True` | удалить: это был no-op (дефолт requests), в публичный контракт не входит |
| Пустые `salePrices` | `MoySkladError` при печати, без фильтрации списка |
| Исключения | `MoySkladError` в `moysklad_manager/exceptions.py`; `AppError` удалить как неиспользуемый |
| `MainWindow` | сигнатура `(print_handler, manager, label_formats, assortment, templates, organization)` |
| Тесты | `tests/test_moysklad_manager.py`, фейковый клиент через monkeypatch `moysklad_manager.manager.MoySkladClient` |
| Версия | `0.2.0` |
| План | этот файл |

## Контракты

`src/moysklad_manager/models.py`:

```python
class Product(BaseModel):
    id: str
    name: str
    meta: dict          # сырой meta из API (нужен для export)
    sale_prices: list[dict]  # сырые salePrices

class LabelTemplate(BaseModel):
    id: str
    name: str
    meta: dict

class Organization(BaseModel):
    id: str
    name: str
    meta: dict
```

`src/moysklad_manager/manager.py`:

```python
class MoySkladManager:
    def __init__(self, token: str): ...   # создаёт MoySkladClient внутри

    def get_assortment(self) -> list[Product]: ...
    def get_custom_templates(self) -> list[LabelTemplate]: ...
    def get_organizations(self) -> list[Organization]: ...

    def request_label(
        self,
        product: Product,
        organization: Organization,
        template: LabelTemplate,
    ) -> bytes: ...
```

Правила реализации:

- `__init__.py` реэкспортирует `MoySkladManager`, модели и `MoySkladError`;
  deprecated-алиасов имён нет (`get_custom_templates`, а не
  `get_assortment_custom_templates`).
- Все три списка читаются одним способом: `client.get(<endpoint>,
  params={"limit": 1000, "offset": offset})` внутри библиотечного `walk(fetch)`;
  `fetch(kwargs)` парсит `response.json()["rows"]` в модели.
- Имя позиции: `row.get("name") or row["meta"].get("name")` (текущий код
  читал `get_json()["meta"]["name"]`, поэтому нужен fallback).
- `client.get/post` возвращают `requests.Response` и **не** вызывают
  `raise_for_status`; статус проверяет адаптер.
- `request_label`: payload
  `{"organization": {"meta": organization.meta}, "count": 1,
  "salePrice": product.sale_prices[0], "template": {"meta": template.meta}}`;
  пустой `sale_prices` → `MoySkladError("Нет цен у товара: <name>")`.
- Редирект `303`: `requests.get(location, timeout=120)` без заголовка
  `Authorization` (URL подписанный, токен туда отправлять нельзя).
- Ошибки: библиотечные `MoySkladError` (импортировать с алиасом),
  `UnauthorizedRequestError`, `MoySkladRateLimitError`,
  `MoySkladConnectionError`, `requests.RequestException`,
  `pydantic.ValidationError`, а также `KeyError`/`IndexError` при разборе
  ответа заворачиваются в `moysklad_manager.exceptions.MoySkladError`
  с контекстом операции. Наружу типы исключений библиотеки не выходят.

## Файлы для создания

- `src/moysklad_manager/__init__.py` — реэкспорт публичного API;
- `src/moysklad_manager/models.py` — `Product`, `LabelTemplate`, `Organization`;
- `src/moysklad_manager/manager.py` — `MoySkladManager`;
- `src/moysklad_manager/exceptions.py` — `MoySkladError`;
- `tests/test_moysklad_manager.py` — тесты (см. ниже).

## Файлы для модификации

- `pyproject.toml`:
  - `version = "0.2.0"`;
  - `description` — вместо MSApi указать moy_sklad;
  - зависимость `MSApi==0.2.11` → `moy_sklad @ git+https://github.com/gusya1/moy_sklad@<tag>`;
  - в `packages` заменить `src/moy_sklad` на `src/moysklad_manager`.
- `src/PrintLabelMS/__main__.py`:
  - убрать импорты `MSApi` и `requests`;
  - `manager = MoySkladManager(config_model.moy_sklad_token)`;
  - загрузка данных через `manager`, передача `manager` в `MainWindow`;
  - `except MoySkladError as e: fatal_error(e)`.
- `src/gui/MainWindow.py`:
  - сигнатура конструктора — с `manager`;
  - имя товара — `product.name` вместо `product.get_json()["meta"]["name"]`;
  - печать — `manager.request_label(product, self.__organization, template)`.
- `README.md` — стек и поток данных (moy_sklad вместо MSApi).
- `AGENTS.md` — §1 (стек), §5 (карта проекта: `src/moysklad_manager`,
  убрать пометку «это НЕ пакет moy_sklad» и упоминания MSApi).
- `docs/architecture.md` — поток данных: токен → `MoySkladManager` →
  ассортимент/шаблоны/организация → `request_label` → PDF.

## Файлы для удаления

- `src/moy_sklad/` (целиком);
- `src/PrintLabelMS/exceptions.py` (`AppError`/`MoySkladError` нигде
  не использовались; `MoySkladError` переезжает в пакет менеджера);
- `tests/test_moy_sklad.py`.

## Тесты

`tests/test_moysklad_manager.py`, фейковый клиент подставляется
monkeypatch'ем `moysklad_manager.manager.MoySkladClient` до создания
менеджера. Сценарии:

1. ассортимент: одна страница, несколько страниц, пустой список;
2. шаблоны и организации: маппинг `id`/`name`/`meta`;
3. `request_label`: `200` → bytes; `303` → редирект без `Authorization`
   (проверять явно); `4xx` → `MoySkladError`; пустые `salePrices` →
   `MoySkladError`;
4. маппинг полей из сырого JSON (включая fallback имени из `meta`);
5. сетевое исключение заворачивается в `MoySkladError`.

GUI-тесты не добавляются.

## Срезы (по одному субагенту за раз)

1. Пакет `moysklad_manager`: модели, исключения, менеджер с тремя
   `get_*` + тесты; `pyproject.toml` (пакеты, временный пин на commit SHA);
2. `request_label` + тесты (`200`/`303`/`4xx`/пустые цены);
3. Проводка: `__main__.py`, `MainWindow.py`, удаление старого пакета и
   `exceptions.py`, удаление старого теста;
4. Документация и версия: README, AGENTS.md, docs/architecture.md,
   `version = "0.2.0"`;
5. Финальный пин на git-тег и проверка установки с чистого venv.

## Проверка

После каждого среза: 1) `pytest`; 2) `ruff check .`.
Срез 5 дополнительно: установка из `pyproject.toml` в чистый venv
(или проверка, что пин разрешается), импорт `moysklad_manager`.
Ручная проверка с реальным `settings.json` — по возможности пользователя
(нужен токен МойСклада).

## Риски

- Тега библиотеки может не быть: мерж блокируется, код остаётся в ветке.
- В ответе `entity/assortment` поле имени может быть только в `meta` —
  поэтому fallback; при отсутствии обоих — `MoySkladError`.
- `salePrices` могут отсутствовать у части ассортимента (услуги) —
  печать такой позиции завершится `MoySkladError`, как и раньше.
- Лимитер библиотеки — 11 запросов / 3 с; при большом ассортименте
  загрузка на старте остаётся синхронной (паритет поведения).
- Python 3.14 и зависимость `ratelimit`: при падении CI сужать матрицу
  по факту, не заранее.

## Актуализация документации

Обновить `README.md`, `AGENTS.md` (стек, карта проекта, поток данных),
`docs/architecture.md` (адаптер `moysklad_manager`, отсутствие MSApi).
История решений остаётся в этом плане.
