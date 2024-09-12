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
        return f'<ip: {self._ip}, port: {self._port}>'
