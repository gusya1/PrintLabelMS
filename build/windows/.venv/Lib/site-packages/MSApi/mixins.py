from MSApi.ObjectMS import check_init


class CodeMixin:
    @check_init
    def get_code(self):
        return self._json.get('code')


class ExternalCodeMixin:
    @check_init
    def get_external_code(self):
        return self._json.get('externalCode')