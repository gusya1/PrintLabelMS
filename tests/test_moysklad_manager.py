import json
from urllib.parse import parse_qs, urlparse
from uuid import UUID, uuid4

import pytest
import requests

from moysklad_manager.exceptions import MoySkladError
from moysklad_manager.manager import MoySkladManager
from moysklad_manager.models import Assortment, LabelTemplate
from moy_sklad.model import MoySkladOrganization


class FakeResponse:
    def __init__(self, status_code=200, rows=None, content=b"", headers=None, json_data=None):
        self.status_code = status_code
        self._rows = rows
        self.content = content
        self.headers = headers or {}
        self._json = json_data

    def json(self):
        if self._json is not None:
            return self._json
        return {"rows": self._rows}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} Error")


class FakeClient:

    """Фейк MoySkladClient: страницы ответов по эндпоинтам, фиксированный ответ на post."""

    def __init__(self, pages=None, post_response=None):
        self.pages = pages or {}
        self.post_response = post_response
        self.get_calls = []
        self.post_calls = []
        self.raise_on_get = None
        self.raise_on_post = None

    def get_by_href(self, href, **kwargs):
        if self.raise_on_get is not None:
            raise self.raise_on_get
        parsed = urlparse(href)
        endpoint = parsed.path.removeprefix("/api/remap/1.2/")
        params = {key: values[0] for key, values in parse_qs(parsed.query).items()}
        offset = int(params.get("offset", 0))
        limit = int(params.get("limit", 1000))
        page_index = offset // limit
        endpoint_pages = self.pages[endpoint]
        rows = endpoint_pages[page_index] if page_index < len(endpoint_pages) else []
        self.get_calls.append((href, params))
        return FakeResponse(200, rows=rows)

    def post(self, request, data=None, **kwargs):
        if self.raise_on_post is not None:
            raise self.raise_on_post
        self.post_calls.append((request, data))
        return self.post_response


def _install_client(monkeypatch, client):
    monkeypatch.setattr("moysklad_manager.manager.MoySkladClient", lambda token: client)
    return MoySkladManager("test-token")


def make_product_row(id=None, name=None, sale_prices=None):
    if id is None:
        id = str(uuid4())
    row = {
        "id": id,
        "meta": {
            "href": f"https://api.moysklad.ru/api/remap/1.2/entity/product/{id}",
            "type": "product",
            "mediaType": "application/json",
        },
    }
    if name is not None:
        row["name"] = name
    if sale_prices is not None:
        row["salePrices"] = sale_prices
    return row


def test_get_assortment_single_page(monkeypatch):
    rows = [make_product_row(name="Товар 1"), make_product_row(name="Товар 2")]
    manager = _install_client(monkeypatch, FakeClient(pages={"entity/assortment": [rows]}))
    products = manager.get_assortment()
    assert all(isinstance(p, Assortment) for p in products)
    assert [str(p.id) for p in products] == [row["id"] for row in rows]
    assert [p.name for p in products] == ["Товар 1", "Товар 2"]


def test_get_assortment_multiple_pages(monkeypatch):
    page_1 = [make_product_row(name=f"Товар {i}") for i in range(1000)]
    page_2 = [make_product_row(name=f"Товар Q{i}") for i in range(3)]
    manager = _install_client(monkeypatch, FakeClient(pages={"entity/assortment": [page_1, page_2]}))
    products = manager.get_assortment()
    assert len(products) == 1003
    assert products[999].name == "Товар 999"
    assert products[1000].name == "Товар Q0"


def test_get_assortment_empty(monkeypatch):
    manager = _install_client(monkeypatch, FakeClient(pages={"entity/assortment": [[]]}))
    assert manager.get_assortment() == []


def test_get_custom_templates_mapping(monkeypatch):
    template_id = str(uuid4())
    rows = [{
        "id": template_id,
        "name": "Шаблон 58x40",
        "meta": {
            "href": f"https://api.moysklad.ru/api/remap/1.2/entity/assortment/metadata/customtemplate/{template_id}",
            "type": "customtemplate",
            "mediaType": "application/json",
        },
    }]
    manager = _install_client(monkeypatch, FakeClient(pages={"entity/assortment/metadata/customtemplate": [rows]}))
    templates = manager.get_custom_templates()
    assert len(templates) == 1
    template = templates[0]
    assert isinstance(template, LabelTemplate)
    assert template.id == UUID(template_id)
    assert template.name == "Шаблон 58x40"
    assert template.meta.type == "customtemplate"


def test_get_organizations_mapping(monkeypatch):
    organization_id = str(uuid4())
    rows = [{
        "id": organization_id,
        "name": "ООО Ромашка",
        "meta": {
            "href": f"https://api.moysklad.ru/api/remap/1.2/entity/organization/{organization_id}",
            "type": "organization",
            "mediaType": "application/json",
        },
    }]
    manager = _install_client(monkeypatch, FakeClient(pages={"entity/organization": [rows]}))
    organizations = manager.get_organizations()
    assert len(organizations) == 1
    organization = organizations[0]
    assert isinstance(organization, MoySkladOrganization)
    assert organization.id == UUID(organization_id)
    assert organization.name == "ООО Ромашка"
    assert organization.meta.type == "organization"


def test_get_assortment_field_mapping(monkeypatch):
    sale_price = {"id": "sp1", "price": 1000, "currencyId": "cur_1"}
    rows = [make_product_row(name="Товар 1", sale_prices=[sale_price])]
    manager = _install_client(monkeypatch, FakeClient(pages={"entity/assortment": [rows]}))
    product = manager.get_assortment()[0]
    assert product.name == "Товар 1"
    assert product.meta.type == "product"
    assert product.salePrices == [sale_price]


def test_get_assortment_missing_name_raises(monkeypatch):
    rows = [{
        "id": str(uuid4()),
        "meta": {"href": "https://api.moysklad.ru/api/remap/1.2/entity/product/x",
                 "type": "product", "mediaType": "application/json"},
    }]
    manager = _install_client(monkeypatch, FakeClient(pages={"entity/assortment": [rows]}))
    with pytest.raises(MoySkladError, match="Загрузка ассортимента"):
        manager.get_assortment()


def test_get_assortment_network_error_wrapped(monkeypatch):
    client = FakeClient(pages={"entity/assortment": [[make_product_row(name="Товар 1")]]})
    client.raise_on_get = requests.exceptions.ConnectionError("сеть недоступна")
    manager = _install_client(monkeypatch, client)
    with pytest.raises(MoySkladError, match="Загрузка ассортимента"):
        manager.get_assortment()


def test_get_assortment_http_error_wrapped(monkeypatch):
    client = FakeClient(pages={"entity/assortment": [[make_product_row(name="Товар 1")]]})
    monkeypatch.setattr(client, "get_by_href", lambda href, **kwargs: FakeResponse(403))
    manager = _install_client(monkeypatch, client)
    with pytest.raises(MoySkladError):
        manager.get_assortment()


def make_product(sale_prices=None):
    if sale_prices is None:
        sale_prices = [{"id": "sp1", "price": 100}]
    return Assortment(
        id="9881531b-9a09-11e6-8af5-581e00000078",
        name="Товар 1",
        meta={
            "href": "https://api.moysklad.ru/api/remap/1.2/entity/product/9881531b-9a09-11e6-8af5-581e00000078",
            "type": "product",
            "mediaType": "application/json",
        },
        salePrices=sale_prices,
    )


def make_template():
    return LabelTemplate(
        id="f47ac10b-58cc-4372-a567-0e02b2c3d479",
        name="Шаблон",
        meta={
            "href": "https://api.moysklad.ru/api/remap/1.2/entity/assortment/metadata/customtemplate/f47ac10b-58cc-4372-a567-0e02b2c3d479",
            "type": "customtemplate",
            "mediaType": "application/json",
        },
    )


def make_organization():
    return MoySkladOrganization(
        id="7c9e6679-7425-40de-bd44-f2dd16c6f047",
        name="ООО Ромашка",
        meta={
            "href": "https://api.moysklad.ru/api/remap/1.2/entity/organization/7c9e6679-7425-40de-bd44-f2dd16c6f047",
            "type": "organization",
            "mediaType": "application/json",
        },
    )


def test_request_label_200(monkeypatch):
    client = FakeClient(post_response=FakeResponse(200, content=b"PDF-DATA"))
    manager = _install_client(monkeypatch, client)
    label_data = manager.request_label(make_product(), make_organization(), make_template())
    assert label_data == b"PDF-DATA"
    request, data = client.post_calls[0]
    assert request == "entity/product/9881531b-9a09-11e6-8af5-581e00000078/export"
    payload = json.loads(data)
    assert payload["count"] == 1
    assert payload["salePrice"] == {"id": "sp1", "price": 100}
    assert payload["organization"]["meta"]["type"] == "organization"
    assert payload["template"]["meta"]["type"] == "customtemplate"


def test_request_label_303_redirect_without_authorization(monkeypatch):
    client = FakeClient(post_response=FakeResponse(303, headers={"Location": "https://signed.example.com/label.pdf"}))
    manager = _install_client(monkeypatch, client)
    captured = {}

    def fake_get(url, **kwargs):
        captured["url"] = url
        captured["headers"] = kwargs.get("headers")
        captured["timeout"] = kwargs.get("timeout")
        return FakeResponse(200, content=b"PDF-FROM-REDIRECT")

    monkeypatch.setattr("moysklad_manager.manager.requests.get", fake_get)
    label_data = manager.request_label(make_product(), make_organization(), make_template())
    assert label_data == b"PDF-FROM-REDIRECT"
    assert captured["url"] == "https://signed.example.com/label.pdf"
    assert captured["timeout"] == 120
    assert "Authorization" not in (captured["headers"] or {})


def test_request_label_303_redirect_error_raises(monkeypatch):
    client = FakeClient(post_response=FakeResponse(303, headers={"Location": "https://signed.example.com/label.pdf"}))
    manager = _install_client(monkeypatch, client)
    monkeypatch.setattr("moysklad_manager.manager.requests.get", lambda url, **kwargs: FakeResponse(404))
    with pytest.raises(MoySkladError, match="Запрос PDF-этикетки"):
        manager.request_label(make_product(), make_organization(), make_template())


def test_request_label_4xx_raises(monkeypatch):
    client = FakeClient(post_response=FakeResponse(400, json_data={"errors": [{"error": "Цена не найдена"}]}))
    manager = _install_client(monkeypatch, client)
    with pytest.raises(MoySkladError, match="Запрос PDF-этикетки.*Цена не найдена"):
        manager.request_label(make_product(), make_organization(), make_template())


def test_request_label_empty_sale_prices_raises(monkeypatch):
    client = FakeClient(post_response=FakeResponse(200, content=b"X"))
    manager = _install_client(monkeypatch, client)
    product = make_product(sale_prices=[])
    with pytest.raises(MoySkladError, match="Нет цен у товара: Товар 1"):
        manager.request_label(product, make_organization(), make_template())
    assert client.post_calls == []


def test_request_label_network_error_wrapped(monkeypatch):
    client = FakeClient(post_response=FakeResponse(200))
    client.raise_on_post = requests.exceptions.ConnectionError("сеть недоступна")
    manager = _install_client(monkeypatch, client)
    with pytest.raises(MoySkladError, match="Запрос PDF-этикетки"):
        manager.request_label(make_product(), make_organization(), make_template())
