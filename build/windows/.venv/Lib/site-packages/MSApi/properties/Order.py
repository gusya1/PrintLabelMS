
class Order:

    def __init__(self):
        self.orders = []

    @classmethod
    def asc(cls, parameter):
        return cls._append_order(Order(), parameter, 'asc')

    @classmethod
    def desc(cls, parameter):
        return cls._append_order(Order(), parameter, 'desc')

    def __str__(self):
        return "order={0}".format(';'.join(self.orders))

    def __add__(self, other):
        self.orders += other.orders
        return self

    @staticmethod
    def _append_order(order_, parameter, operator):
        order_.orders.append(f"{parameter},{operator}")
        return order_
