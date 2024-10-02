import socket
from typing import Any
import select

from pack4.utils.Address import Address


class Socket:
    _BUFF_SIZE = 8096

    def __init__(self, addr, timeout_sec: float):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self._socket.bind(("", 0))
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # self._timeout = timeout_sec
        # self._socket.settimeout(timeout_sec)
        self._socket.setblocking(False)


        try:
            address_info = socket.getaddrinfo(addr.ip, None)[0]
        except socket.gaierror:
            raise Exception("invalid address")

        self._group = socket.inet_pton(address_info[0], address_info[4][0])

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

    @property
    def port(self):
        return self._socket.getsockname()[1]

    @property
    def ip(self):
        return self._socket.getsockname()[0]

    def send(self, msg, addr: Address):
        self._socket.sendto(msg, (addr.ip, addr.port))

    def receive(self) -> tuple[Any, Address] | None:
        rd_socks, wr_socks, _ = select.select([self._socket], [], [], 0)
        for s in rd_socks:
            data, sender = s.recvfrom(self._BUFF_SIZE)
            return data, Address(sender[0], sender[1])

    def close(self):
        self._socket.close()
