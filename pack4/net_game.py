import sys
import threading
from collections.abc import Iterable

import pygame

import snakes_pb2 as pb2
from pack4.controller.game_controller import GameController
from pack4.game_models.apple import Apple
from pack4.game_models.game_field import Field
from pack4.game_models.snake import Snake
from pack4.node_roles.deputy import DeputyNode
from pack4.node_roles.empty import EmptyNode
from pack4.node_roles.master import MasterNode
from pack4.node_roles.normal import NormalNode
from pack4.node_roles.viewer import ViewerNode
from pack4.utils.Address import Address
from pack4.utils.config_reader import Settings, GameConfig
from pack4.view.button import GameButton
from pack4.view.side_table import SideTable


class NetGame:
    APPLE_COLOR = (255, 0, 0)
    SNAKE_COLOR = (0, 255, 0)
    BLACK_COLOR = (0, 0, 0)
    WHITE_COLOR = (255, 255, 255)

    def __init__(self, addr: Address, config: Settings):
        self._addr = addr
        self._node: EmptyNode | ViewerNode | NormalNode | DeputyNode | MasterNode = EmptyNode(addr, config)
        self._config = config
        self._game_controller = GameController(Field(self._config.width, self._config.height, self._config.cell_size),
                                               {}, [])
        self._cell_size = config.cell_size
        pygame.init()
        self._side_table = SideTable(config.width * self._config.cell_size, 0, 200, config.height * self._config.cell_size)
        self._screen = pygame.display.set_mode(
            (config.width * config.cell_size + self._side_table.width, config.height * config.cell_size))
        self._interrupted = False
        self._exited = False

    def _create_new_game(self):
        self._node = MasterNode(self._addr, self._config, self._game_controller)

    def _resize_screen(self, width, height):
        self._side_table = SideTable(width * self._config.cell_size, 0, 200, height * self._config.cell_size)
        self._screen = pygame.display.set_mode(
            (width * self._config.cell_size + self._side_table.width, height * self._config.cell_size))

    def _run_empty(self):
        res = self._node.get_received_to_multicast_addr()
        if res is not None:
            self._node.handle_message(res[0], res[1])

        # if len(self._node.announcements) > 0:
        #     try:
        #         print("joined")
        #         self._node = self._node.join_game_request(pb2.NodeRole.NORMAL, res[1])
        #         self._interrupted = True
        #         return
        #     except ConnectionError as e:
        #         print(e)

    def _run_viewer(self):

        res = self._node.get_received_to_multicast_addr()
        while res is not None:
            self._node.handle_message(res[0], res[1])
            res = self._node.get_received_to_multicast_addr()

        res = self._node.get_received_to_main_socket()
        while res is not None:
            self._node.handle_message(res[0], res[1])
            res = self._node.get_received_to_main_socket()

        try:
            self._node.check_master_status()
        except ConnectionError as e:
            print(e)
            exit(1)
        self._node.ping_master_if_needed()

    def _run_master(self):
        self._node.send_out_announcement()
        self._node.send_out_curr_game_state(self._game_controller.snakes, self._game_controller.apples)

        msg = self._node.get_received_to_main_socket()
        while msg is not None:
            self._node.handle_message(msg[0], msg[1])
            msg = self._node.get_received_to_main_socket()

        self._node.check_players_state()

    def _run_normal_or_deputy(self):
        res = self._node.get_received_to_multicast_addr()

        while res is not None:
            self._node.handle_message(res[0], res[1])
            res = self._node.get_received_to_multicast_addr()

        res = self._node.get_received_to_main_socket()
        while res is not None:
            new_node = self._node.handle_message(res[0], res[1])
            if new_node is not None:
                self._node = new_node
                self._interrupted = True
                return
            res = self._node.get_received_to_main_socket()
        res = self._node.check_master_status()
        if res is not None:
            self._node = res
            self._interrupted = True
            return
        self._node.ping_master_if_needed()

    @staticmethod
    def _get_direction_from_button(key):
        match key:
            case pygame.K_DOWN:
                return Snake.Direction.UP
            case pygame.K_UP:
                return Snake.Direction.DOWN
            case pygame.K_RIGHT:
                return Snake.Direction.RIGHT
            case pygame.K_LEFT:
                return Snake.Direction.LEFT
            case _:
                return None

    def _keyboard_interaction_master(self):

        for event in pygame.event.get()[::-1]:
            if event.type == pygame.KEYDOWN:
                if self._node.player_id not in self._game_controller.snakes:
                    return
                direction = self._get_direction_from_button(event.key)
                if direction is not None:
                    self._game_controller.snakes[self._node.player_id].set_direction(direction)
                break
            if event.type == pygame.QUIT:
                self._exited = True
                pygame.quit()
                sys.exit()

    def _keyboard_interaction_viewer(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()

    def _keyboard_interaction_normal(self):
        for event in pygame.event.get()[::-1]:
            if event.type == pygame.KEYDOWN:
                direction = self._get_direction_from_button(event.key)
                if direction is not None:
                    self._node.request_change_direction(direction)
                break
            if event.type == pygame.QUIT:
                self._exited = True
                pygame.quit()
                sys.exit()

    def _draw_objects(self, snakes: Iterable[Snake], apples: Iterable[Apple]):
        for snake in snakes:
            for coord in snake.coords:
                pygame.draw.rect(self._screen,
                                 self.SNAKE_COLOR,
                                 pygame.Rect(coord[0], coord[1], self._cell_size, self._cell_size))

        for apple in apples:
            pygame.draw.rect(self._screen,
                             self.APPLE_COLOR,
                             pygame.Rect(apple.coords[0], apple.coords[1], self._cell_size, self._cell_size))

        self._side_table.draw(self._screen, self._node.score())

    def _master_game(self):

        if len(self._game_controller.snakes) == 0:
            self._game_controller.add_snake(self._node.player_id, self._config.user_name)

        while not self._interrupted:

            while len(self._game_controller.apples) < self._config.food_static + len(self._game_controller.snakes):
                try:
                    self._game_controller.add_apple()
                except Exception:
                    break

            self._screen.fill(self.BLACK_COLOR)

            self._draw_objects(self._game_controller.snakes.values(), self._game_controller.apples)

            self._keyboard_interaction_master()

            self._game_controller.move_snakes()
            res = self._game_controller.check_apples()
            for id in res:
                self._game_controller.add_points(1, id)

            collided_ids = self._game_controller.check_collisions()

            for id in collided_ids:
                if collided_ids[id] is not None:
                    self._game_controller.add_points(1, collided_ids[id])
                self._game_controller.remove_snake(id)
                self._node.change_player_role(id, pb2.NodeRole.VIEWER)

            if len(self._game_controller.snakes) == 0:
                self._node.send_out_curr_game_state(self._game_controller.snakes, self._game_controller.apples)
                self._exited = True

            pygame.display.update()
            pygame.time.Clock().tick(10)

    def _viewer_game(self):
        while not self._interrupted:
            self._screen.fill(self.BLACK_COLOR)
            snakes, apples = self._node.get_curr_game_objects()
            self._draw_objects(snakes, apples)

            self._keyboard_interaction_viewer()

            pygame.display.update()
            pygame.time.Clock().tick(60)

    def _normal_game(self):
        while not self._interrupted:
            self._screen.fill(self.BLACK_COLOR)
            snakes, apples = self._node.get_curr_game_objects()
            self._draw_objects(snakes, apples)

            self._keyboard_interaction_normal()

            pygame.display.update()
            pygame.time.Clock().tick(60)

    def _empty_game(self):
        button_width = 200
        button_height = 40
        step = 10
        curr_start_x = self._config.width * self._config.cell_size - button_width * 2 - step * 2
        curr_start_y = step
        buttons = []

        def create_game_wrapper():
            self._create_new_game()
            self._interrupted = True

        def join_game_wrapper(role, addr):
            try:

                if isinstance(self._node, EmptyNode):
                    self._node = self._node.join_game_request(role, addr)
                    self._interrupted = True
                return
            except ConnectionError as e:
                print(e)

        buttons.append(GameButton("начать новую", (self._config.width * self._config.cell_size - button_width) // 2,
                                  self._config.height * self._config.cell_size - step - button_height, button_width,
                                  button_height, self.APPLE_COLOR, create_game_wrapper))

        while not self._interrupted:

            if len(buttons) < 10:
                for addr, announce in list(self._node.announcements.items())[len(buttons) - 1:10]:
                    name = announce.announcement.games[0].game_name
                    buttons.append(
                        GameButton(name + '(игрок)', curr_start_x, curr_start_y, button_width, button_height,
                                   self.SNAKE_COLOR,
                                   join_game_wrapper, pb2.NodeRole.NORMAL, addr))
                    buttons.append(
                        GameButton(name + '(зритель)', curr_start_x + step + button_width, curr_start_y, button_width,
                                   button_height, self.WHITE_COLOR,
                                   join_game_wrapper, pb2.NodeRole.VIEWER, addr))
                    curr_start_y += step + button_height

            self._screen.fill(self.BLACK_COLOR)

            for button in buttons:
                button.draw(self._screen)

            for ev in pygame.event.get():

                if ev.type == pygame.QUIT:
                    self._exited = True
                    pygame.quit()

                if ev.type == pygame.MOUSEBUTTONDOWN:
                    mouse = pygame.mouse.get_pos()
                    for button in buttons:
                        if button.collide(mouse[0], mouse[1]):
                            button.run_func()
                            pygame.display.update()
                            break

            pygame.display.update()
            pygame.time.Clock().tick(60)

    def run_game(self):
        while True:
            print(f'curr role {type(self._node)}')
            self._interrupted = False
            match self._node:
                case NormalNode() | DeputyNode():
                    self._normal_game()
                case MasterNode():
                    self._master_game()
                case ViewerNode():
                    self._viewer_game()
                case EmptyNode():
                    self._empty_game()

            if not isinstance(self._node, MasterNode):
                width, height = self._node.get_width_height()
            else:
                width, height = self._config.width, self._config.height
                self._game_controller = self._node._game_controller
            self._resize_screen(width, height)

    def run(self):
        threading.Thread(target=self.run_node).start()
        self.run_game()

    def run_node(self):
        while not self._exited:
            match self._node:
                case EmptyNode():
                    self._run_empty()
                case NormalNode():
                    self._run_normal_or_deputy()
                case ViewerNode():
                    self._run_viewer()
                case DeputyNode():
                    self._run_normal_or_deputy()
                case MasterNode():
                    self._run_master()
                case _:
                    pass


multicast_addr = "239.192.0.4"
port = 9192
addr = Address(multicast_addr, port)

if __name__ == '__main__':
    config = GameConfig(50, 50, 1, 500, "game", "kest", 10)
    game = NetGame(addr, config)
    game.run()
