import socket

from pack2.address import Address


class Sender:

    def __init__(self, address: Address):
        self._address = address.ip
        self._port = address.port
        self._connected = False
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)

    def connect(self):
        if not self._connected:
            try:
                self._socket.connect((self._address, self._port))
                self._connected = True
            except socket.error:
                raise ConnectionRefusedError('Failed to connect to server')

    def close(self):
        if self._connected:
            self._connected = False
            self._socket.close()

    def send(self, data: bytes):
        if not self._connected:
            self.connect()
        self._socket.send(data)

    def response(self) -> bytes:
        return self._socket.recv(1)
