class Frame:
    """
    A single CAN frame.
    """

    def __init__(self, id=0, data=None, extended=False,
                 transmission_request=False,
                 data_length=0):

        if data is None:
            data = bytes()

        if len(data) > 8:
            raise ValueError

        self.id = id

        self.data = data
        self.data_length = data_length

        if len(self.data) > 0:
            self.data_length = len(self.data)

        self.transmission_request = transmission_request
        self.extended = extended

    def __eq__(self, other):
        return self.id == other.id and self.data == other.data
