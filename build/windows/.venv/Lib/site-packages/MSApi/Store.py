import warnings

from MSApi.MSLowApi import MSLowApi, caching
from MSApi.ObjectMS import ObjectMS, check_init
from MSApi.mixin.GenListMixin import GenerateListMixin


class Store(ObjectMS,
            GenerateListMixin):
    _type_name = 'store'

    @classmethod
    @caching
    def generate(cls, **kwargs):
        warnings.warn("deprecated", DeprecationWarning)
        return MSLowApi.gen_objects('entity/store', Store, **kwargs)

    def __init__(self, json):
        super().__init__(json)

    @check_init
    def get_name(self) -> str:
        return self._json.get('name')

    @check_init
    def get_id(self) -> str:
        return self._json.get('id')
