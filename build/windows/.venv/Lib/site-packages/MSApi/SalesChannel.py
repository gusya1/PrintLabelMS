from MSApi import ObjectMS

from MSApi.mixin.GenListMixin import GenerateListMixin
from MSApi.mixin.CreateNewMixin import CreateNewMixin
from MSApi.mixin.AccountIdMixin import AccountIdMixin
from MSApi.mixin.ArchivedMixin import ArchivedMixin
from MSApi.mixin.DescriptionMixin import DescriptionMixin
from MSApi.mixin.GroupMixin import GroupMixin
from MSApi.mixin.NameMixin import NameMixin
from MSApi.mixins import CodeMixin, ExternalCodeMixin


class SalesChannel(ObjectMS,
                   CreateNewMixin,
                   GenerateListMixin,
                   AccountIdMixin,
                   ArchivedMixin,
                   CodeMixin,
                   DescriptionMixin,
                   ExternalCodeMixin,
                   GroupMixin,
                   NameMixin,
                   ):
    _type_name = 'saleschannel'
