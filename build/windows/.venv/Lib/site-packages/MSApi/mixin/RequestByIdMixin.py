from MSApi.MSLowApi import MSLowApi, error_handler, caching


class RequestByIdMixin:

    @classmethod
    @caching
    def request_by_id(cls, id):
        response = MSLowApi.auch_get('entity/{}/{}'.format(cls._type_name, id))
        error_handler(response)
        return cls(response.json())
