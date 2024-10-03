import socket
from typing import Any

import select

from pack4.utils.Address import Address


class MulticastReceiverSocket:
    _BUFF_SIZE = 8096
    LOOPBACK = True

    def __init__(self, multicast_addr: Address, timeout):
        self._address = multicast_addr.ip
        self._port = multicast_addr.port
        try:
            address_info = socket.getaddrinfo(self._address, None)[0]
        except socket.gaierror:
            raise Exception("invalid address")

        self._socket = socket.socket(address_info[0], socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # self._socket.settimeout(timeout)
        self._socket.setblocking(False)
        self._socket.bind(('', self._port))

        self._group = socket.inet_pton(address_info[0], address_info[4][0])

        if address_info[0] == socket.AF_INET:
            opt_value = self._group + socket.INADDR_ANY.to_bytes(4, "big")
            self._socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, opt_value)
        else:
            interface = 0
            opt_value = self._group + interface.to_bytes(4, "big")
            self._socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, opt_value)

        self._socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, self.LOOPBACK)

    def receive(self) -> tuple[Any, Address] | None:
        rd_socks, wr_socks, _ = select.select([self._socket], [], [], 0)
        try:
            for s in rd_socks:
                data, sender = s.recvfrom(self._BUFF_SIZE)
                return data, Address(sender[0], sender[1])
        except Exception as e:
            return None
        # try:
        #
        #     data, sender = self._socket.recvfrom(self._BUFF_SIZE)
        #     return data, Address(sender[0], sender[1])
        # except Exception:
        #     return None

    def close(self):
        self._socket.close()
