import pathlib
import socket
import netifaces
from netifaces import interfaces

from pack2.address import Address
from pack2.file import FileToSend
from pack2.sender import Sender


class ClientApp:
    _buff_size = 4096 * 8
    _SUCCESS = 0
    _FAILURE = 1

    def __init__(self, file_path: str, host: str, port: int):
        self._file_path = file_path
        self._ip = host if self._is_ipv4(host) else socket.gethostbyname(host)
        self._port = port
        self._sender = Sender(Address(self._ip, self._port))

    @staticmethod
    def _is_ipv4(ip: str):
        a = ip.split('.')
        for i in a:
            if not (0 <= int(i) <= 255):
                return False
        return True

    def send_file(self, name):
        file_info = FileToSend(name, self._file_path)
        buffer = b''
        buffer += file_info.raw_header()
        print('подключение к серверу')
        try:
            self._sender.connect()
        except ConnectionError:
            print('не удалось подключиться к серверу')
            return

        print("передача файла")
        with open(self._file_path, "rb") as raw_file:
            while True:
                buffer += raw_file.read(self._buff_size - len(buffer))
                if len(buffer) == 0:
                    break
                try:
                    self._sender.send(buffer)
                except Exception as e:
                    print(e)
                    print('передача файла остановлена')
                    return
                buffer = b''

        response = self._sender.response()
        if response is None:
            print("не удалось проверить целостность файла, сервер не отвечает")
            self._sender.close()
            return

        if int.from_bytes(response, "big") == self._SUCCESS:
            print("файл успешно передан")
        else:
            print('файл был поврежден при передаче')
        self._sender.close()


if __name__ == '__main__':
    full_path = r"C:\Users\anzhi\netPacks\packs\pack2\test.exe"
    path = pathlib.Path(full_path)
    app = ClientApp(full_path, "10.9.40.124", 1999)
    app.send_file(path.name)
