
class Expand:

    def __init__(self, *args):
        self.expand_list: [str] = []
        for arg in args:
            self.expand_list.append(str(arg))

    def __str__(self):
        return f"expand={','.join(self.expand_list)}"
