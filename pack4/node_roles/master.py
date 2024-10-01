import time
from typing import Any

import pack4.snakes_pb2 as pb2
from pack4.utils.Address import Address
from pack4.controller.game_controller import GameController
from pack4.game_models.apple import Apple
from pack4.game_models.snake import Snake
from pack4.node_roles.base import Base
from pack4.net.sender_socket import Socket


class MasterNode(Base):
    ROLE = pb2.NodeRole.MASTER
    STATE_ORDER = 0

    def __init__(self, addr, config, game_controller: GameController, main_socket: Socket = None, player_id=None,
                 players=None,
                 state_order_start=0, pb2_config=None):

        self._player_id = player_id if player_id is not None else 0
        max_player_id = self._player_id
        if players is not None:
            for player in players:
                max_player_id = max(player.id, max_player_id)

        super().__init__(addr, config, player_id, main_socket, max_player_id + 1)
        self._game_name = config.game_name
        self._can_join = True
        self._pb_config = pb2.GameConfig(width=config.width,
                                         height=config.height,
                                         food_static=config.food_static,
                                         state_delay_ms=config.state_delay_ms) if pb2_config is None else pb2_config
        self._players = [pb2.GamePlayer(name=self._player_name,
                                        id=self._player_id,
                                        role=self._role,
                                        score=0)] if players is None else players
        self._game_controller = game_controller
        if len(self._game_controller.score()) == 0:
            self._game_controller.score()[config.user_name] = 0
        self._last_player_message_time: dict[int, float] = {}
        self._last_player_message_seq: dict[int, int] = {}
        self.STATE_ORDER = state_order_start
        self._last_state_time = 0
        self._last_announce_time = 0
        self._STATE_DELAY_MS = config.state_delay_ms
        self._TIME_TO_DIE = self._STATE_DELAY_MS * 0.8

    @property
    def player_id(self):
        return self._player_id

    def _update_last_message_time(self, player_id):
        self._last_player_message_time[player_id] = time.time()

    def _promote_player(self, player, new_role: pb2.NodeRole):
        msg = pb2.GameMessage(msg_seq=next(self.msg_seq_gen), receiver_id=player.id, sender_id=self._player_id)
        role_change = pb2.GameMessage.RoleChangeMsg(sender_role=pb2.NodeRole.MASTER, receiver_role=new_role)
        msg.role_change.CopyFrom(role_change)
        self._main_socket.send(msg.SerializeToString(), Address(player.ip_address, player.port))
        self._main_socket.send(msg.SerializeToString(), Address(player.ip_address, player.port))

    def score(self) -> dict[str, int]:
        return self._game_controller.score()

    def change_player_role(self, player_id, role):
        if player_id == self.player_id:
            return
        for player in self._players:
            if player.id == player_id:
                self._promote_player(player, role)
                break

    def check_players_state(self):
        now = time.time()
        updated_players = []
        actual_deputy = None
        potential_deputy = None
        for player in self._players:
            if player.id == self._player_id:
                updated_players.append(player)
                continue

            if player.id not in self._last_player_message_time:
                self._last_player_message_time[player.id] = now
                updated_players.append(player)
                if player.role != pb2.NodeRole.VIEWER:
                    potential_deputy = player
                continue

            if abs(now - self._last_player_message_time[player.id]) > self._TIME_TO_DIE:
                match player.role:
                    case pb2.NodeRole.NORMAL:
                        continue
                    case pb2.NodeRole.VIEWER:
                        continue
                    case pb2.NodeRole.DEPUTY:
                        actual_deputy = None

            else:
                if player.role == pb2.NodeRole.DEPUTY:
                    actual_deputy = player

                if potential_deputy is None:
                    potential_deputy = player

                updated_players.append(player)

        if actual_deputy is None and potential_deputy is not None:
            potential_deputy.role = pb2.NodeRole.DEPUTY
            self._promote_player(potential_deputy, pb2.NodeRole.DEPUTY)

        self._players = updated_players

    def _create_announcement(self):
        game_announcement = pb2.GameAnnouncement(players=pb2.GamePlayers(players=self._players),
                                                 config=self._pb_config,
                                                 can_join=self._can_join,
                                                 game_name=self._game_name)

        game_announcement = pb2.GameMessage.AnnouncementMsg(games=[game_announcement])
        msg_to_send = pb2.GameMessage(msg_seq=next(self.msg_seq_gen))
        msg_to_send.announcement.CopyFrom(game_announcement)
        return msg_to_send

    def send_out_announcement(self):
        now = time.time()
        if now - self._last_announce_time >= 1:

            msg = self._create_announcement()
            self._main_socket.send(msg.SerializeToString(), self._multicast_addr)
            self._last_announce_time = now

    def send_out_curr_game_state(self, snakes: dict[int: Snake], apples: list[Apple]):
        if (time.time() - self._last_state_time) * 1000 < self._STATE_DELAY_MS:
            return
        self.STATE_ORDER += 1
        foods = [pb2.GameState.Coord(x=apple.x_coord, y=apple.y_coord) for apple in apples]
        snakes_pb2 = []

        for player_id, snake in snakes.items():
            if snake.zombie:
                state = pb2.GameState.Snake.SnakeState.ZOMBIE
            else:
                state = pb2.GameState.Snake.SnakeState.ALIVE

            head_direction: pb2.Direction = 0
            match snake.direction:
                case Snake.Direction.DOWN:
                    head_direction = pb2.Direction.DOWN
                case Snake.Direction.RIGHT:
                    head_direction = pb2.Direction.RIGHT
                case Snake.Direction.LEFT:
                    head_direction = pb2.Direction.LEFT
                case Snake.Direction.UP:
                    head_direction = pb2.Direction.UP

            snakes_pb2.append(pb2.GameState.Snake(player_id=player_id,
                                                  points=[pb2.GameState.Coord(x=coord[0], y=coord[1]) for coord in
                                                          snake.coords],
                                                  state=state,
                                                  head_direction=head_direction
                                                  ))

        msg = pb2.GameMessage(msg_seq=next(self.msg_seq_gen))
        for player in self._players:
            if player.name in self.score():
                player.score = self.score()[player.name]

        new_score = {}
        score = self.score()
        score.clear()
        for player in self._players:
            if player.role == pb2.NodeRole.VIEWER:
                continue
            else:
                new_score[player.name] = player.score
        score.update(new_score)
        state_msg = pb2.GameMessage.StateMsg(state=
            pb2.GameState(foods=foods, state_order=self.STATE_ORDER, players=pb2.GamePlayers(players=self._players),
                          snakes=snakes_pb2))
        msg.state.CopyFrom(state_msg)

        self.STATE_ORDER += 1
        self._main_socket.send(msg.SerializeToString(), self._multicast_addr)

    def _handle_join_message(self, join_msg, msg_seq: int, addr: Address):
        role = join_msg.requested_role
        name = join_msg.player_name
        id = next(self.player_id_gen)
        ip_address = addr.ip
        port = addr.port

        msg = pb2.GameMessage(msg_seq=msg_seq, receiver_id=id, sender_id=self._player_id)

        match role:
            case pb2.NodeRole.VIEWER | pb2.NodeRole.NORMAL:

                if pb2.NodeRole.NORMAL == role and len(self._players) == self._MAX_PLAYERS_NUM:
                    error = pb2.GameMessage.ErrorMsg(error_message="max number of players already in game")
                    msg.error.CopyFrom(error)
                else:
                    self._players.append(pb2.GamePlayer(name=name,
                                                        id=id,
                                                        role=role,
                                                        ip_address=ip_address,
                                                        port=port,
                                                        score=0))
                    if role == pb2.NodeRole.NORMAL:
                        self._game_controller.add_snake(id, name)

                    ack = pb2.GameMessage.AckMsg()
                    msg.ack.CopyFrom(ack)

                    self._update_last_message_time(id)

            case _:
                error = pb2.GameMessage.ErrorMsg(error_message="forbidden player role")
                msg.error.CopyFrom(error)

        self._main_socket.send(msg.SerializeToString(), addr)

    def _handle_change_direction_request(self, game_msg, addr: Address):
        new_direction = game_msg.steer.direction
        msg_seq = game_msg.msg_seq
        player_id = game_msg.sender_id

        self._update_last_message_time(player_id)

        response = pb2.GameMessage(msg_seq=msg_seq, sender_id=self._player_id, receiver_id=player_id)

        if player_id not in self._game_controller.snakes or self._game_controller.snakes[player_id].zombie:
            err = pb2.GameMessage.ErrorMsg(error_message=f"player with id {player_id} doesn't have alive snake")
            response.error.CopyFrom(err)
        else:
            if player_id not in self._last_player_message_seq or self._last_player_message_seq[player_id] < msg_seq:
                self._last_player_message_seq[player_id] = msg_seq
                self._game_controller.snakes[player_id].set_direction(new_direction)

            ack = pb2.GameMessage.AckMsg()
            response.ack.CopyFrom(ack)

        self._main_socket.send(response.SerializeToString(), addr)

    def _handle_ping_message(self, msg, addr):
        # msg_seq = msg.msg_seq
        sender_id = msg.sender_id
        # res = pb2.GameMessage(msg_seq=msg_seq)
        # ping = pb2.GameMessage.Ping()
        # res.ping.CopyFrom(ping)

        self._update_last_message_time(sender_id)

        # self._main_socket.send(res.SerializeToString(), addr)

    def _handle_discover_msg(self, addr):
        msg = self._create_announcement()
        self._main_socket.send(msg.SerializeToString(), addr)

    def handle_message(self, msg: pb2.GameMessage, addr: Address) -> Any:
        match msg.WhichOneof('Type'):
            case "discover":
                self._handle_discover_msg(addr)
            case "join":
                self._handle_join_message(msg.join, msg.msg_seq, addr)
            case "steer":
                self._handle_change_direction_request(msg, addr)
            case "ping":
                self._handle_ping_message(msg, addr)

    def name_by_id(self, player_id) -> str:
        for player in self._players:
            if player.id == player_id:
                return player.name
        return ""

    def get_received_to_main_socket(self) -> tuple[pb2.GameMessage, Address] | None:

        res = self._main_socket.receive()
        if res is None:
            return None

        data, addr = res

        parsed = pb2.GameMessage()
        try:
            parsed.ParseFromString(data)
            return parsed, addr
        except Exception as e:
            return None

# multicast_addr = "239.192.0.4"
# port = 9192
# addr = Address(multicast_addr, port)
# m = MasterNode(addr, config)
# print(m._role)
