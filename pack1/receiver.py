import json
import socket
from types import SimpleNamespace
from typing import Any

import message


class Receiver:
    _BUFF_SIZE = 4096
    _TIME_OUT = 0.1

    def __init__(self, address: str, port: int):
        self._address = address
        self._port = port
        try:
            address_info = socket.getaddrinfo(address, None)[0]
        except socket.gaierror:
            raise Exception("invalid address")

        self._socket = socket.socket(address_info[0], socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind(('', port))

        self._socket.settimeout(self._TIME_OUT)

        self._group = socket.inet_pton(address_info[0], address_info[4][0])

        if address_info[0] == socket.AF_INET:
            opt_value = self._group + socket.INADDR_ANY.to_bytes(4, "big")
            self._socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, opt_value)
        else:
            interface = 0
            opt_value = self._group + interface.to_bytes(4, "big")
            self._socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, opt_value)

    def receive(self) -> (message.Message | None, Any):
        try:
            data, sender = self._socket.recvfrom(self._BUFF_SIZE)
            msg = json.loads(data.decode("utf-8"), object_hook=lambda d: SimpleNamespace(**d))
            return msg, sender
        except socket.timeout as e:
            return None, None

    def close(self):
        self._socket.close()
