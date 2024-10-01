import socket
from typing import Any


from pack4.utils.Address import Address


class Socket:
    _BUFF_SIZE = 8096

    def __init__(self, timeout_sec: float):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self._socket.bind(("", 0))
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._timeout = timeout_sec
        self._socket.settimeout(timeout_sec)

    @property
    def port(self):
        return self._socket.getsockname()[1]

    @property
    def ip(self):
        return self._socket.getsockname()[0]

    def send(self, msg, addr: Address):
        self._socket.sendto(msg, (addr.ip, addr.port))

    def receive(self) -> tuple[Any, Address] | None:
        try:
            data, sender = self._socket.recvfrom(self._BUFF_SIZE)
            return data, Address(sender[0], sender[1])
        except Exception:
            return None

    def close(self):
        self._socket.close()
