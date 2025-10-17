
from typing import Optional
from MSApi.ObjectMS import ObjectMS, check_init
from MSApi.Employee import Employee
from MSApi.mixin.GenListMixin import GenerateListMixin


class Project(ObjectMS, GenerateListMixin):
    _type_name = 'project'

    def __init__(self, json):
        super().__init__(json)

    @check_init
    def get_id(self) -> str:
        return self._json.get('id')

    @check_init
    def get_account_id(self) -> str:
        return self._json.get('accountId')

    @check_init
    def get_owner(self) -> Optional[Employee]:
        return self._get_optional_object('owner', Employee)

    @check_init
    def get_shared(self) -> bool:
        return self._json.get('shared')

    @check_init
    def get_name(self) -> str:
        return self._json.get('name')

    @check_init
    def get_description(self) -> Optional[str]:
        return self._json.get('description')

    @check_init
    def get_code(self) -> Optional[str]:
        return self._json.get('code')

    @check_init
    def get_external_code(self) -> Optional[str]:
        return self._json.get('externalCode')

    @check_init
    def get_external_code(self) -> str:
        return self._json.get('externalCode')

    @check_init
    def is_archived(self) -> bool:
        return self._json.get('archived')

