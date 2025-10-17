import urllib.parse


class Filter(object):

    @classmethod
    def eq(cls, parameter, data):
        return cls._append_filter(Filter(), "=", parameter, data)

    @classmethod
    def gt(cls, parameter, data):
        return cls._append_filter(Filter(), ">", parameter, data)

    @classmethod
    def lt(cls, parameter, data):
        return cls._append_filter(Filter(), "<", parameter, data)

    @classmethod
    def gte(cls, parameter, data):
        return cls._append_filter(Filter(), ">=", parameter, data)

    @classmethod
    def lte(cls, parameter, data):
        return cls._append_filter(Filter(), "<=", parameter, data)

    @classmethod
    def ne(cls, parameter, data):
        return cls._append_filter(Filter(), "!=", parameter, data)

    @classmethod
    def siml(cls, parameter, data):
        return cls._append_filter(Filter(), "~=", parameter, data)

    @classmethod
    def simr(cls, parameter, data):
        return cls._append_filter(Filter(), "=~", parameter, data)

    @classmethod
    def sim(cls, parameter, data):
        return cls._append_filter(Filter(), "~", parameter, data)

    @classmethod
    def exists(cls, parameter, exists=True):
        operator = '!=' if exists else '='
        f = Filter()
        f.filters.append(f"{parameter}{operator}")
        return f

    def __init__(self):
        self.filters = []

    def __str__(self):
        return "filter={0}".format(';'.join(self.filters))

    def __add__(self, other):
        self.filters += other.filters
        return self

    @staticmethod
    def _append_filter(filter_, operator, parameter, data):
        filter_.filters.append(f"{parameter}{operator}{urllib.parse.quote(str(data))}")
        return filter_
