import random


class ViciousList(list):

    def __getitem__(self, item):
        if isinstance(item, int):
            if len(self) == 0:
                raise IndexError("attempt to get value of empty list")
            else:
                return super().__getitem__(item % len(self))
        else:
            raise IndexError("index must be an integer")

    def __setitem__(self, key, value):
        if isinstance(key, int):
            if len(self) == 0:
                raise IndexError("attempt to get value of empty list")
            else:
                return super().__setitem__(key % len(self), value)
        else:
            raise IndexError("index must be an integer")

class Field:

    _FREE = 0
    _TAKEN = 1

    def __init__(self, width, height, cell_size):
        self._cell_size = cell_size
        self._width = width
        self._height = height
        self._cells: ViciousList = ViciousList([ViciousList([self._FREE for _ in range(width)]) for _ in range(height)])

    def _get_random_start(self) -> tuple:
        return random.randint(0, self._width), random.randint(0, self._height)

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    @property
    def cell_size(self):
        return self._cell_size

    def __getitem__(self, index):
        return self._cells[index % self._height]

    def set_cell(self, row: int, col: int):
        self._cells[row][col] = self._TAKEN

    def set_multiple(self, coords: list[tuple[int, int]]):
        for coord in coords:
            self._cells[coord[1]][coord[0]] = self._TAKEN

    def clear_cell(self, row: int, col: int):
        self._cells[row][col] = self._FREE

    def _get_place_with_start(self, start: tuple, end: tuple, size) -> tuple | None:
        start_x = start[0]
        for y in range(start[1], end[1]):
            for x in range(start_x, end[0]):
                flag = True

                for i in range(x, x + size):
                    if not flag:
                        break

                    for j in range(y, y + size):
                        if self._cells[j][i] == self._TAKEN:
                            flag = False
                            break

                if flag:
                    return x, y

            start_x = 0

    def _get_place_for_new_obj(self, size) -> tuple[int, int] | None:
        start_x, start_y = self._get_random_start()
        start = self._get_place_with_start((start_x, start_y), (self._width, self._height), size)

        if start is not None:
            return start[0] * self._cell_size, start[1] * self._cell_size

        start = self._get_place_with_start((0, 0), (self._width, start_y), size)

        if start is not None:
            return start[0] * self._cell_size, start[1] * self._cell_size

    def get_place_for_new_snake(self) -> tuple[int, int] | None:
        return self._get_place_for_new_obj(5)

    def get_place_for_new_apple(self) -> tuple[int, int] | None:
        return self._get_place_for_new_obj(1)

    def __repr__(self):
        return '\n'.join(' '.join(map(str, item)) for item in self._cells)

