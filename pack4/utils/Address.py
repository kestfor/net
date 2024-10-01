class Address:

    def __init__(self, ip: str, port: int):
        self._ip = ip
        self._port = port

    @property
    def ip(self):
        return self._ip

    @property
    def port(self):
        return self._port

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self._ip}:{self._port}>"

    def __hash__(self):
        return hash(f'{self._ip}:{self._port}')

    def __eq__(self, other):
        if isinstance(other, Address):
            return self.ip == other.ip and self.port == other.port
        return False
