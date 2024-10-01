from pack4.game_models.apple import Apple


class Snake:
    class Direction:
        UP = 1
        DOWN = 2
        LEFT = 3
        RIGHT = 4

    def __init__(self, start_x, start_y, field_height, field_width, cell_size, body: list[tuple[int, int]] = None,
                 direction=Direction.RIGHT):
        self._coords: list[tuple[int, int]] = [(start_x, start_y)] if body is None else body
        self._direction = direction
        self._field_height = field_height
        self._field_width = field_width
        self._cell_size = cell_size
        self.zombie = False

    @property
    def direction(self):
        return self._direction

    @property
    def coords(self):
        return self._coords.copy()

    def add_tail(self, tail: tuple[int, int]):
        self._coords.append(tail)

    def set_direction(self, direction):
        if self._direction == self.Direction.RIGHT and direction == self.Direction.LEFT:
            return

        if self._direction == self.Direction.LEFT and direction == self.Direction.RIGHT:
            return

        if self._direction == self.Direction.UP and direction == self.Direction.DOWN:
            return

        if self._direction == self.Direction.DOWN and direction == self.Direction.UP:
            return

        self._direction = direction

    def __getitem__(self, item):
        return self._coords[item]

    def self_collide(self):
        if len(set(self.coords)) < len(self._coords):
            print('self collide')
            return True
        return False

    def crash_into(self, other) -> bool:
        if isinstance(other, Snake):
            if len(set(other._coords).intersection(set(self._coords[0]))) > 0:
                return True
            else:
                return False
        return False

    def crash_into_cell(self, other) -> tuple[int, int] | None:
        if isinstance(other, Snake):
            res = set(other._coords).intersection({self._coords[0]})
            if len(res) > 0:
                return res.pop()
            else:
                return None
        return None

    def collide(self, other) -> bool:
        if isinstance(other, Snake):
            if len(set(other._coords).intersection({self._coords})) > 0:
                return True
            else:
                return False
        return False

    def __contains__(self, item: tuple[int, int] | Apple) -> bool:
        if isinstance(item, tuple):
            return item in self._coords
        elif isinstance(item, Apple):
            return item.coords in self._coords
        else:
            raise TypeError

    def move(self) -> (tuple, tuple):  # returns (removed coords, new coords)
        match self._direction:
            case self.Direction.UP:
                new_coords = self._coords[0][0], (self._coords[0][1] + self._cell_size) % (
                        self._field_height * self._cell_size)
            case self.Direction.DOWN:
                new_coords = self._coords[0][0], (self._coords[0][1] - self._cell_size) % (
                        self._field_height * self._cell_size)
            case self.Direction.LEFT:
                new_coords = (self._coords[0][0] - self._cell_size) % (self._field_width * self._cell_size), \
                    self._coords[0][1]
            case self.Direction.RIGHT:
                new_coords = (self._coords[0][0] + self._cell_size) % (self._field_width * self._cell_size), \
                    self._coords[0][1]
            case _:
                raise ValueError
        old = self._coords.pop()
        self._coords.insert(0, new_coords)
        return old, new_coords
