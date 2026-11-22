from moy_sklad.client import MoySkladClient, make_url
from moy_sklad.getters import walk_for_href

from .models import Assortment, LabelTemplate


def get_assortment(client: MoySkladClient, **kwargs):
    """Обход коллекции ассортимента. Возвращает генератор позиций."""
    return walk_for_href(
        client,
        Assortment,
        make_url("entity/assortment"),
        **kwargs,
    )


def get_custom_templates(client: MoySkladClient, **kwargs):
    """Обход кастомных шаблонов этикетки. Возвращает генератор шаблонов."""
    return walk_for_href(
        client,
        LabelTemplate,
        make_url("entity/assortment/metadata/customtemplate"),
        **kwargs,
    )
