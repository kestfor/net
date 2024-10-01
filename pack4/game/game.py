import sys

import pygame

from pack4.controller.game_controller import GameController
from pack4.game_models.apple import Apple
from pack4.game_models.game_field import Field
from pack4.game_models.snake import Snake


class Game:
    APPLE_COLOR = (255, 0, 0)
    SNAKE_COLOR = (0, 255, 0)
    BLACK_COLOR = (0, 0, 0)

    def __init__(self, config, cell_size: int = 20):

        self._cell_size = cell_size
        self._config = config
        self._field = Field(config.width, config.height, cell_size)
        self._apples: list[Apple] = []
        self._snakes: dict[int: Snake] = {}
        self._controller = GameController(self._field, self._snakes, self._apples)
        pygame.init()
        self._screen = pygame.display.set_mode((config.width * cell_size, config.height * cell_size))

    def keyboard_interaction(self):
        for event in pygame.event.get()[::-1]:
            if event.type == pygame.KEYDOWN:
                match event.key:
                    case pygame.K_DOWN:
                        self._snakes[0].set_direction(Snake.Direction.UP)
                    case pygame.K_UP:
                        self._snakes[0].set_direction(Snake.Direction.DOWN)
                    case pygame.K_RIGHT:
                        self._snakes[0].set_direction(Snake.Direction.RIGHT)
                    case pygame.K_LEFT:
                        self._snakes[0].set_direction(Snake.Direction.LEFT)
                break
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

    def run_master(self):

        if len(self._snakes) == 0:
            self._controller.add_snake(0)

        if len(self._apples) == 0:
            self._controller.add_apple()

        while True:
            self._screen.fill(self.BLACK_COLOR)

            for snake in self._snakes.values():
                for coord in snake.coords:
                    pygame.draw.rect(self._screen,
                                     self.SNAKE_COLOR,
                                     pygame.Rect(coord[0], coord[1], self._cell_size, self._cell_size))

            for apple in self._apples:
                pygame.draw.rect(self._screen,
                                 self.APPLE_COLOR,
                                 pygame.Rect(apple.coords[0], apple.coords[1], self._cell_size, self._cell_size))

            self.keyboard_interaction()

            self._controller.move_snakes()
            res = self._controller.check_apples()

            if len(res) > 0:
                self._controller.add_apple()

            collided_ids = self._controller.check_collisions()

            if len(collided_ids) > 0:
                pygame.quit()
                sys.exit()

            pygame.display.update()
            pygame.time.Clock().tick(10)
            break

# gameConfig = Settings()
# g = Game(gameConfig)
# while True:
#     g.run_master()
