from random import randint, choice

from pack4.game_models.apple import Apple
from pack4.game_models.game_field import Field
from pack4.game_models.snake import Snake


class GameController:

    def __init__(self, field: Field, snakes: dict[int, Snake], apples: list[Apple], scores=None, names=None):
        self._field = field
        self._snakes: dict[int: Snake] = snakes  # key - player_id, value - snake_object
        self._old_tails: dict[int, tuple[int, int]] = {}
        self._apples = apples
        self.names: dict[int: str] = {} if names is None else names
        self._scores: dict[str: int] = {} if scores is None else scores

    def add_points(self, points: int, player_id: int):
        self._scores[self.names[player_id]] += points

    def score(self):
        return self._scores

    def get_points(self, player_id: str) -> int:
        return self._scores[self.names[player_id]]

    def add_snake(self, player_id: int, player_name) -> Snake:

        self.names[player_id] = player_name
        coords: tuple[int, int] = self._field.get_place_for_new_snake()
        if coords is None:
            raise ValueError("no place for new snake")

        start_direction = choice(
            [Snake.Direction.UP, Snake.Direction.DOWN, Snake.Direction.LEFT, Snake.Direction.RIGHT])
        tail_coords: tuple[int, int] = (0, 0)
        match start_direction:
            case Snake.Direction.UP:
                tail_coords = coords[0], coords[1] - 1
            case Snake.Direction.DOWN:
                tail_coords = coords[0], coords[1] + 1
            case Snake.Direction.LEFT:
                tail_coords = coords[0] + 1, coords[1]
            case Snake.Direction.RIGHT:
                tail_coords = coords[0] - 1, coords[1]

        snake = Snake(0, 0, self._field.height, self._field.width, self._field.cell_size, body=[coords, tail_coords],
                      direction=start_direction)
        self._snakes[player_id] = snake
        self._old_tails[player_id] = coords
        self._scores[self.names[player_id]] = 0
        return snake

    @property
    def snakes(self):
        return self._snakes

    @property
    def apples(self):
        return self._apples

    def add_apple(self) -> Apple:

        coords = self._field.get_place_for_new_apple()
        if coords is None:
            raise ValueError("no place for new apple")

        res = Apple(coords)
        self._apples.append(res)
        return res

    def remove_snake(self, player_id: int):
        snake = self._snakes.pop(player_id, None)
        self._scores.pop(self.names[player_id], None)
        self._old_tails.pop(player_id, None)
        for coords in snake.coords:
            if randint(0, 1) == 0:
                self.apples.append(Apple(coords))

    def check_collisions(self) -> dict[int: int]:
        """key - id of crashed snake. key - id of snake in which crashed, None if head-head"""
        players = list(self._snakes.keys())
        res = {}
        for i in range(len(players)):
            if self._snakes[players[i]].self_collide():
                res[players[i]] = None

            for j in range(i + 1, len(players)):
                first_cell = self._snakes[players[i]].crash_into_cell(self._snakes[players[j]])
                second_cell = self._snakes[players[j]].crash_into_cell(self._snakes[players[i]])

                if first_cell == second_cell and first_cell is not None:
                    res[players[i]] = None
                    res[players[j]] = None

                else:
                    if first_cell is not None:
                        res[players[i]] = players[j]

                    if second_cell is not None:
                        res[players[j]] = players[i]
        return res

    def move_snakes(self):
        for id, snake in self._snakes.items():
            old, new = snake.move()
            self._old_tails[id] = old

            self._field.clear_cell(old[1] // self._field.cell_size, old[0] // self._field.cell_size)
            self._field.set_cell(new[1] // self._field.cell_size, new[0] // self._field.cell_size)

    def check_apples(self) -> dict[int: tuple[int, int]]:
        res = {}
        for apple in self._apples:
            for id, snake in self._snakes.items():
                if apple.coords == snake.coords[0]:
                    res[id] = apple.coords
                    self._apples.remove(apple)

                    tail = self._old_tails[id]
                    snake.add_tail(tail)

                    self._field.set_cell(tail[0] // self._field.cell_size, tail[1] // self._field.cell_size)
        return res
