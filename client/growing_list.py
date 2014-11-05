class GrowingList(list):
    def __init__(self, default_value=None, iterable=[]):
        list.__init__(self, iterable)
        self.default_value = default_value

    def __setitem__(self, index, value):
        if index >= len(self):
            missing_length = index + 1 - len(self)
            self.extend([self.default_value] * missing_length)
        list.__setitem__(self, index, value)
