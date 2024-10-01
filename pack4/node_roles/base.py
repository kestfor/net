import time
from typing import Any

import pack4.snakes_pb2 as pb2
from pack4.utils.Address import Address
from pack4.utils.config_reader import Settings
from pack4.net.receiver_socket import MulticastReceiverSocket
from pack4.net.sender_socket import Socket


class Base:
    _ANNOUNCEMENT_INTERVAL = 1
    _MAX_PLAYERS_NUM = 10
    _STATE_DELAY_MS = 10
    _TIME_TO_DIE = _STATE_DELAY_MS * 0.8
    ROLE = pb2.NodeRole.NORMAL

    @staticmethod
    def get_msg_seq(start=0):
        i = start
        while True:
            yield i
            i += 1

    @staticmethod
    def get_player_id(start=0):
        i = start
        while True:
            yield i
            i += 1

    def __init__(self, addr, config: Settings, player_id=None, main_socket: Socket = None, player_id_start=0,
                 msg_seq_start=0):
        self._non_parsed_config = config
        self._addr = addr
        self._multicast_addr = addr
        self._multicast_receiver = MulticastReceiverSocket(addr, self._STATE_DELAY_MS // 10 / 1000)
        self._main_socket = Socket(self._STATE_DELAY_MS // 10 / 1000) if main_socket is None else main_socket
        self._main_socket.receive()
        self._player_name = config.user_name
        self.player_id_gen = self.get_player_id(player_id_start)
        self.msg_seq_gen = self.get_msg_seq(msg_seq_start)
        self._player_id = next(self.player_id_gen) if player_id is None else player_id
        self._role = self.ROLE
        self._announcements = {}
        self._last_recv_time = time.time()
        self._scores = {}

    @property
    def announcements(self):
        return self._announcements

    def score(self):
        return self._scores

    def handle_message(self, msg: pb2.GameMessage, addr: Address) -> Any:

        match msg.WhichOneof("Type"):
            case "announcement":
                self._announcements[addr] = msg
            case _:
                return

    def get_received_to_multicast_addr(self) -> tuple[pb2.GameMessage, Address] | None:

        res = self._multicast_receiver.receive()
        if res is None:
            return None

        self._last_recv_time = time.time()

        data, addr = res
        parsed = pb2.GameMessage()
        try:
            parsed.ParseFromString(data)
            return parsed, addr
        except Exception as e:
            return None
