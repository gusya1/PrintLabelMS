
from MSApi.properties.Filter import Filter
import datetime


class DateTimeFilter(Filter):

    @classmethod
    def eq(cls, parameter: str, data: datetime.datetime):
        return cls._append_filter(Filter(), "=", parameter, cls.format_datetime(data))

    @classmethod
    def gt(cls, parameter: str, data: datetime.datetime):
        return cls._append_filter(Filter(), ">", parameter, cls.format_datetime(data))

    @classmethod
    def lt(cls, parameter: str, data: datetime.datetime):
        return cls._append_filter(Filter(), "<", parameter, cls.format_datetime(data))

    @classmethod
    def gte(cls, parameter: str, data: datetime.datetime):
        return cls._append_filter(Filter(), ">=", parameter, cls.format_datetime(data))

    @classmethod
    def lte(cls, parameter: str, data: datetime.datetime):
        return cls._append_filter(Filter(), "<=", parameter, cls.format_datetime(data))

    @classmethod
    def ne(cls, parameter: str, data: datetime.datetime):
        return cls._append_filter(Filter(), "!=", parameter, cls.format_datetime(data))

    @classmethod
    def siml(cls, parameter: str, data: datetime.datetime):
        return cls._append_filter(Filter(), "~=", parameter, cls.format_datetime(data))

    @classmethod
    def simr(cls, parameter: str, data: datetime.datetime):
        return cls._append_filter(Filter(), "=~", parameter, cls.format_datetime(data))

    @classmethod
    def sim(cls, parameter: str, data: datetime.datetime):
        return cls._append_filter(Filter(), "~", parameter, cls.format_datetime(data))

    def __init__(self):
        super().__init__()

    def __str__(self):
        return "filter={0}".format(';'.join(self.filters))

    def __add__(self, other):
        self.filters += other.filters
        return self

    @staticmethod
    def format_datetime(date):
        return date.strftime('%Y-%m-%d %H:%M:%S')