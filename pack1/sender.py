import json
import socket

from message import Message, MessageEncoder


class Sender:
    INADDR_ANY = '0.0.0.0'

    def __init__(self, address: str, port: int):
        self._address = address
        self._port = port

        try:
            address_info = socket.getaddrinfo(self._address, None)[0]
        except socket.gaierror:
            raise Exception("invalid address")

        self._socket = socket.socket(address_info[0], socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self._group = socket.inet_pton(address_info[0], address_info[4][0])

        # mreq = struct.pack(
        #     "4s4s", socket.inet_aton(self._address),
        #     socket.inet_aton(self.INADDR_ANY),)
        # self._socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        ttl = 1
        ttl = ttl.to_bytes(1, "big")

        if address_info[0] == socket.AF_INET:
            opt_value = self._group + socket.INADDR_ANY.to_bytes(4, "big")
            self._socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, opt_value)
            self._socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
        else:
            interface = 0
            opt_value = self._group + interface.to_bytes(4, "big")
            self._socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, opt_value)
            self._socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, ttl)

    def send(self, msg: Message):
        self._socket.sendto(json.dumps(msg, cls=MessageEncoder).encode("utf-8"), (self._address, self._port))

    def close(self):
        self._socket.close()
