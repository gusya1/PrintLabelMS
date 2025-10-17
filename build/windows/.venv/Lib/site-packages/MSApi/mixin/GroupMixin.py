from typing import Optional

from MSApi.ObjectMS import check_init
from MSApi.Group import Group


class GroupMixin:

    @check_init
    def get_group(self) -> Optional[Group]:
        """Группа"""
        result = self._json.get('group')
        if result is None:
            return None
        return Group(result)
