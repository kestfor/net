import socket

from pack2.address import Address


class Receiver:

    def __init__(self, address: Address):
        self._port = address.port
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)

    def listen(self):
        self._socket.bind(("", self._port))
        self._socket.listen(5)

    def accept(self) -> tuple[socket, Address]:
        sock, (addr, port) = self._socket.accept()
        return sock, Address(addr, port)
