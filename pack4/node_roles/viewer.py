import time
from typing import Any, Iterable

import pack4.snakes_pb2 as pb2
from pack4.utils.Address import Address
from pack4.game_models.apple import Apple
from pack4.game_models.snake import Snake
from pack4.node_roles.base import Base


class ViewerNode(Base):
    ROLE = pb2.NodeRole.VIEWER

    def __init__(self, addr, config, player_id, master_addr: Address, main_socket, pb2_config):
        super().__init__(addr, config, player_id, main_socket)
        self._game_state: pb2.GameState = None
        self._last_game_state_id = 0
        self._master_addr = master_addr
        self._pb2_config = pb2_config
        self._deputy_addr: Address | None = None
        self._STATE_DELAY_MS = pb2_config.state_delay_ms
        self._TIME_TO_DIE = self._STATE_DELAY_MS * 0.8
        self._score = {}

    def _update_deputy(self):
        for player in self._game_state.players.players:
            if player.role == pb2.NodeRole.DEPUTY:
                self._deputy_addr = Address(player.ip_address, player.port)

    def check_master_status(self):
        now = time.time()
        if (now - self._last_recv_time) * 1000 > self._TIME_TO_DIE:
            if self._deputy_addr is None:
                raise ConnectionError("игра завершена")
            self._master_addr = self._deputy_addr

    def get_curr_game_objects(self) -> tuple[Iterable[Snake], Iterable[Apple]]:
        game_state = self._game_state
        if game_state is None:
            return [], []
        width = self._pb2_config.width
        height = self._pb2_config.height
        snakes_pb2 = game_state.snakes
        apples_pb2 = game_state.foods
        snakes: list[Snake] = []
        apples: list[Apple] = []
        for snake in snakes_pb2:
            snakes.append(Snake(0, 0, height, width,
                                self._non_parsed_config.cell_size,
                                [(coord.x, coord.y) for coord in snake.points],
                                snake.head_direction))

        for apple in apples_pb2:
            apples.append(Apple((apple.x, apple.y)))
        return snakes, apples

    def _update_score(self):
        if self._game_state is None:
            return
        self._score = {}
        for player in self._game_state.players.players:
            if player.role == pb2.NodeRole.VIEWER:
                continue
            self._score[player.name] = player.score

    def score(self):
        self._update_score()
        return self._score

    def get_width_height(self) -> tuple[int, int]:
        width = self._pb2_config.width
        height = self._pb2_config.height
        return width, height

    def handle_message(self, msg: pb2.GameMessage, addr: Address) -> Any:
        match msg.WhichOneof("Type"):
            case "state":
                if self._last_game_state_id < msg.state.state.state_order:
                    self._game_state = msg.state.state
                    self._last_game_state_id = msg.state.state.state_order
                    self._update_deputy()
                self._send_ack(msg.msg_seq, 0, 0, addr)
            case "role_change":

                self._send_ack(msg.msg_seq, 0, 0, addr)

                sender_role = msg.role_change.sender_role

                if sender_role == pb2.NodeRole.MASTER:
                    self._master_addr = addr
            case "ping":
                return
            case _:
                return

    def ping_master_if_needed(self):
        now = time.time()
        if (now - self._last_send_time) * 1000 > self._STATE_DELAY_MS / 10:
            self._ping_node(self._master_addr)

    def _ping_node(self, addr):
        msg = pb2.GameMessage(msg_seq=next(self.msg_seq_gen), sender_id=self._player_id)
        ping = pb2.GameMessage.PingMsg()
        msg.ping.CopyFrom(ping)
        self._main_socket.send(msg.SerializeToString(), addr)
        self._last_send_time = time.time()

    def get_received_to_main_socket(self) -> tuple[pb2.GameMessage, Address] | None:

        res = self._main_socket.receive()
        if res is None:
            return

        self._last_recv_time = time.time()
        data, addr = res

        parsed = pb2.GameMessage()
        try:
            parsed.ParseFromString(data)
            return parsed, addr
        except Exception as e:
            return None