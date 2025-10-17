from typing import Optional

from MSApi.Attribute import Attribute
from MSApi.ObjectMS import check_init
from MSApi.MSLowApi import MSLowApi, error_handler


class AttributeMixin:

    @classmethod
    def gen_attributes_list(cls):
        response = MSLowApi.auch_get("entity/{}/metadata/attributes".format(cls._type_name))
        error_handler(response)
        for attribute_json in response.json()["rows"]:
            yield Attribute(attribute_json)

    @check_init
    def gen_attributes(self):
        for attr in self._json.get('attributes', []):
            yield Attribute(attr)

    def get_attribute_by_name(self, name: str) -> Optional[Attribute]:
        for attr in self.gen_attributes():
            if attr.get_name() == name:
                return attr
        return None