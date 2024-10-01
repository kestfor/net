import time

import pack4.snakes_pb2 as pb2
from pack4.utils.Address import Address
from pack4.node_roles.base import Base
from pack4.node_roles.normal import NormalNode
from pack4.node_roles.viewer import ViewerNode


class EmptyNode(Base):

    def _create_join_msg(self, role, game_name):
        msg = pb2.GameMessage(msg_seq=next(self.msg_seq_gen))
        join_msg = pb2.GameMessage.JoinMsg(player_name=self._player_name, game_name=game_name, requested_role=role)
        msg.join.CopyFrom(join_msg)
        return msg

    def join_game_request(self, role, addr: Address) -> ViewerNode | NormalNode:
        announcement = self._announcements[addr].announcement.games[0]
        game_name = announcement.game_name
        msg = self._create_join_msg(role, game_name)
        self._main_socket.send(msg.SerializeToString(), addr)

        t = time.time()

        res = None
        while res is None and ((time.time() - t) * 1000 < self._TIME_TO_DIE):
            res = self._main_socket.receive()

        if res is None:
            raise ConnectionError("can't connect to host")

        response, addr = res

        parsed = pb2.GameMessage()
        parsed.ParseFromString(response)

        match parsed.WhichOneof("Type"):
            case "ack":
                self._player_id = parsed.receiver_id
                match role:
                    case pb2.NodeRole.VIEWER:
                        return ViewerNode(self._addr, self._non_parsed_config, self._player_id, addr, self._main_socket,
                                          announcement.config)
                    case pb2.NodeRole.NORMAL:
                        return NormalNode(self._addr, self._non_parsed_config, self._player_id, addr, self._main_socket,
                                          announcement.config)
                    # case pb2.NoderRole.DEPUTY:
                    #     return DeputyNode(self._addr, self._non_parsed_config, self._player_id)
            case "error":
                raise ConnectionRefusedError(parsed.error.error_message)
            case _:
                raise ConnectionError("unsupported message type response to join request")
