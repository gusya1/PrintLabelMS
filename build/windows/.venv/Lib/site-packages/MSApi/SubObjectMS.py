
class SubObjectMS:
    def __init__(self, json):
        self._json = json

    def get_json(self):
        return self._json

    def _get_optional_object(self, name, impl):
        result = self._json.get(name)
        if result is not None:
            return impl(result)
        return None
