import socket


class SocketReader:

    def __init__(self, sock: socket.socket, timeout: float):
        self._socket = sock
        self._socket.settimeout(timeout)

    def read(self, n: int) -> bytes | None:
        try:
            data = self._socket.recv(n)
            if data == b'':
                raise ConnectionAbortedError('socket was closed')
            return data
        except socket.timeout as e:
            return None
