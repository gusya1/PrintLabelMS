import json

import requests
from pydantic import ValidationError
from moy_sklad.client import MoySkladClient, raise_for_status
from moy_sklad.exceptions import (
    MoySkladConnectionError as LibraryMoySkladConnectionError,
    MoySkladError as LibraryMoySkladError,
    MoySkladRateLimitError as LibraryMoySkladRateLimitError,
    UnauthorizedRequestError as LibraryUnauthorizedRequestError,
)
from moy_sklad.getters import walk_for_all
from moy_sklad.model import MoySkladOrganization
from moy_sklad.utils import make_entity_meta_field

from .exceptions import MoySkladError
from .getters import get_assortment, get_custom_templates
from .models import Assortment, LabelTemplate

_API_ERRORS = (
    LibraryMoySkladError,
    LibraryUnauthorizedRequestError,
    LibraryMoySkladRateLimitError,
    LibraryMoySkladConnectionError,
    requests.RequestException,
    ValidationError,
    KeyError,
    IndexError,
)


class MoySkladManager:

    """Адаптер над библиотекой moy_sklad для PrintLabelMS."""

    def __init__(self, token: str):
        self.__client = MoySkladClient(token)

    def get_assortment(self) -> list[Assortment]:
        try:
            return list(get_assortment(self.__client))
        except _API_ERRORS as e:
            raise MoySkladError(f"Загрузка ассортимента: {e}") from e

    def get_custom_templates(self) -> list[LabelTemplate]:
        try:
            return list(get_custom_templates(self.__client))
        except _API_ERRORS as e:
            raise MoySkladError(f"Загрузка шаблонов этикеток: {e}") from e

    def get_organizations(self) -> list[MoySkladOrganization]:
        try:
            return list(walk_for_all(self.__client, MoySkladOrganization))
        except _API_ERRORS as e:
            raise MoySkladError(f"Загрузка организаций: {e}") from e

    def request_label(
        self,
        product: Assortment,
        organization: MoySkladOrganization,
        template: LabelTemplate,
    ) -> bytes:
        if not product.salePrices:
            raise MoySkladError(f"Нет цен у товара: {product.name}")
        payload = {
            "organization": make_entity_meta_field(organization).model_dump(),
            "count": 1,
            "salePrice": product.salePrices[0],
            "template": make_entity_meta_field(template).model_dump(),
        }
        operation = f"Запрос PDF-этикетки для товара {product.name}"
        try:
            response = self.__client.post(f"entity/{product.meta.type}/{product.id}/export", json.dumps(payload))
            if response.status_code == 303:
                location = response.headers["Location"]
                redirect_response = requests.get(location, timeout=120)
                if redirect_response.status_code != 200:
                    raise_for_status(redirect_response)
                return redirect_response.content
            if response.status_code != 200:
                raise_for_status(response)
            return response.content
        except _API_ERRORS as e:
            raise MoySkladError(f"{operation}: {e}") from e
