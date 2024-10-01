class Apple:

    def __init__(self, coords: tuple[int, int]):

        self._coords = coords

    @property
    def coords(self):
        return self._coords

    @property
    def x_coord(self):
        return self._coords[0]

    @property
    def y_coord(self):
        return self._coords[1]