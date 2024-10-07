import time
from typing import Any

import pack4.node_roles.deputy as dp
import pack4.node_roles.viewer as v
import pack4.snakes_pb2 as pb2
from pack4.utils.Address import Address
from pack4.game_models.snake import Snake
from utils.msg_to_resend import MsgToResend


class NormalNode(v.ViewerNode):
    ROLE = pb2.NodeRole.NORMAL

    def __init__(self, addr, config, player_id, master_addr: Address, main_socket, pb2_config):
        super().__init__(addr, config, player_id, master_addr, main_socket, pb2_config)

    # def recv_ack_wrapper(self) -> tuple[bytes, Address]:
    #     res = None
    #     while res is None or (time.time() - self._last_recv_time) * 1000 < self._TIME_TO_DIE:
    #         res = self._main_socket.receive()
    #
    #     if res is None:
    #         raise ConnectionError("can't receive response, node is dead")
    #
    #     self._last_recv_time = time.time()
    #     return res

    # def check_master_status(self):
    #     now = time.time()
    #     if (now - self._last_recv_time) * 1000 > self._TIME_TO_DIE:
    #         if self._deputy_addr is None:
    #             raise ConnectionError("игра завершена")
    #         self._master_addr = self._deputy_addr

    def granted(self, msg_seq: int):
        return msg_seq not in self._acks

    def request_change_direction(self, direction: Snake.Direction) -> int:
        """return msg_seq that later may be used to know if change was granted"""
        msg_seq = next(self.msg_seq_gen)
        msg = pb2.GameMessage(msg_seq=msg_seq, sender_id=self._player_id)
        steer_msg = pb2.GameMessage.SteerMsg(direction=direction)
        msg.steer.CopyFrom(steer_msg)

        self._acks[msg_seq] = MsgToResend(msg.SerializeToString(), self._master_addr)
        self._main_socket.send(self._acks[msg_seq].msg, self._acks[msg_seq].addr)
        self._last_send_time = time.time()
        return msg_seq

    def handle_message(self, msg: pb2.GameMessage, addr: Address) -> Any:
        super().handle_message(msg, addr)
        match msg.WhichOneof("Type"):
            case "role_change":
                sender_role = msg.role_change.sender_role
                receiver_role = msg.role_change.receiver_role

                if receiver_role == pb2.NodeRole.DEPUTY:

                    return dp.DeputyNode(self._addr, self._non_parsed_config, self._player_id, self._master_addr,
                                         self._main_socket, self._pb2_config)

                if receiver_role == pb2.NodeRole.VIEWER:
                    return v.ViewerNode(self._addr, self._non_parsed_config, self._player_id, self._master_addr,
                                        self._main_socket, self._pb2_config)
            case 'error':
                raise ConnectionError(msg.error.error_message)
            case _:
                return
