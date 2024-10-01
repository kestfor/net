import time
from typing import Any

import pack4.node_roles.master as m
import pack4.node_roles.normal as n
import pack4.snakes_pb2 as pb2
from pack4.utils.Address import Address
from pack4.controller.game_controller import GameController
from pack4.game_models.apple import Apple
from pack4.game_models.game_field import Field
from pack4.game_models.snake import Snake


class DeputyNode(n.NormalNode):
    ROLE = pb2.NodeRole.DEPUTY

    def _send_promote_yourself_news(self, player):
        msg = pb2.GameMessage(msg_seq=next(self.msg_seq_gen), sender_id=self._player_id, receiver_id=player.id)
        role_change = pb2.GameMessage.RoleChangeMsg(sender_role=pb2.NodeRole.MASTER, receiver_role=player.role)
        msg.role_change.CopyFrom(role_change)
        self._main_socket.send(msg.SerializeToString(), Address(player.ip_address, player.port))

    def _create_game_controller(self) -> GameController:
        game_state = self._game_state
        width = self._pb2_config.width
        height = self._pb2_config.height
        snakes_pb2 = game_state.snakes
        apples_pb2 = game_state.foods
        snakes: dict[int: Snake] = {}
        apples: list[Apple] = []
        score = {}
        players = self._game_state.players.players
        for player in players:
            score[player.name] = player.score
        field = Field(self._non_parsed_config.width, self._non_parsed_config.height, self._non_parsed_config.cell_size)
        for snake in snakes_pb2:
            snakes[snake.player_id] = Snake(0, 0, height, width,
                                            self._non_parsed_config.cell_size,
                                            [(coord.x, coord.y) for coord in snake.points],
                                            snake.head_direction)
            field.set_multiple(snakes[snake.player_id].coords)

        for apple in apples_pb2:
            apples.append(Apple((apple.x, apple.y)))
            field.set_cell(apple.y, apple.x)

        return GameController(field, snakes, apples, score)

    def check_master_status(self) -> None | m.MasterNode:
        now = time.time()
        if (now - self._last_recv_time) * 1000 > self._TIME_TO_DIE:
            return self._create_master()

    def _create_master(self) -> m.MasterNode:
        new_players = []
        players = self._game_state.players.players
        for player in players:
            if player.role == pb2.NodeRole.MASTER:
                continue

            if player.id == self._player_id:
                player.role = pb2.NodeRole.MASTER

            new_players.append(player)
            self._send_promote_yourself_news(player)
        return m.MasterNode(self._addr, self._non_parsed_config, self._create_game_controller(), self._main_socket,
                            self._player_id,
                            new_players,
                            self._last_game_state_id + 1, self._pb2_config)

    def handle_message(self, msg: pb2.GameMessage, addr: Address) -> Any:
        res = super().handle_message(msg, addr)
        if res is not None:
            return res
        match msg.WhichOneof("Type"):
            case "role_change":
                sender_role = msg.role_change.sender_role
                receiver_role = msg.role_change.receiver_role

                if receiver_role == pb2.NodeRole.MASTER:
                    return self._create_master()
            case _:
                return
