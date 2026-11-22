from uuid import UUID

from pydantic import BaseModel

from moy_sklad.model import MoySkladAssortment, MoySkladMeta


class Assortment(MoySkladAssortment):

    """Позиция ассортимента МойСклада (эндпоинт entity/assortment)."""

    salePrices: list[dict] = []


class LabelTemplate(BaseModel):

    """Кастомный шаблон этикетки (entity/assortment/metadata/customtemplate)."""

    id: UUID
    meta: MoySkladMeta
    name: str
