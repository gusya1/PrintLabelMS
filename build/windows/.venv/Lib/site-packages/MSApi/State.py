
from MSApi.ObjectMS import ObjectMS, check_init


class State(ObjectMS):
    def __init__(self, json):
        super().__init__(json)

    @check_init
    def get_id(self) -> str:
        return self._json.get('id')

    @check_init
    def get_account_id(self) -> str:
        return self._json.get('accountId')

    @check_init
    def get_name(self) -> str:
        return self._json.get('name')

    @check_init
    def get_color(self) -> str:
        return self._json.get('color')

    @check_init
    def get_state_type(self) -> str:
        return self._json.get('stateType')

    @check_init
    def get_entity_type(self) -> str:
        return self._json.get('entityType')
