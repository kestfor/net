import json
import socket
import struct

from pack1.message import Message, MessageEncoder


class Sender:

    def __init__(self, address: str, port: int):
        self._address = address
        self._port = port

        try:
            address_info = socket.getaddrinfo(self._address, None)[0]
        except socket.gaierror:
            raise Exception("invalid address")

        self._socket = socket.socket(address_info[0], socket.SOCK_DGRAM)

        ttl = 1
        ttl = ttl.to_bytes(1, "big")

        if address_info[0] == socket.AF_INET:
            self._socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
        else:
            self._socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, ttl)

    def send(self, msg: Message):
        self._socket.sendto(json.dumps(msg, cls=MessageEncoder).encode("utf-8"), (self._address, self._port))

    def close(self):
        self._socket.close()


