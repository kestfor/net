import os
import sys
import time
from socket import socket
from threading import Thread

from pack2.address import Address
from pack2.file import FileToReceive
from pack2.receiver import Receiver
from pack2.socket_reader import SocketReader


class ServerApp:
    _dir = 'uploads'
    _buff_size = 8192
    _timeout_to_read = 0.5
    _max_attempts = 5

    _SUCCESS = b'\x00'
    _FAILURE = b'\x01'

    def __init__(self, port: int):
        self._receiver = Receiver(Address("", port))
        try:
            os.mkdir(self._dir)
        except FileExistsError:
            pass

    @staticmethod
    def _uniquify(path):
        filename, extension = os.path.splitext(path)
        counter = 1

        while os.path.exists(path):
            path = filename + " (" + str(counter) + ")" + extension
            counter += 1

        return path

    def _get_data(self, reader: SocketReader) -> bytes:
        attempts = 0
        buffer = None
        while buffer is None:
            attempts += 1
            buffer = reader.read(self._buff_size)

            if attempts > self._max_attempts:
                raise ConnectionError("нет данных от пользователя")

            if buffer is None:
                print("попытка получить данные от пользователя №", attempts + 1)

        return buffer

    def _handle_new_connection(self, sock: socket, addr: Address):
        reader = SocketReader(sock, self._timeout_to_read)

        try:
            buffer = self._get_data(reader)
        except ConnectionError as e:
            print(e)
            return

        print('новое подключение', addr)

        try:
            file_info = FileToReceive(buffer)
        except RuntimeError:
            print("can't read file")
            return

        last_time = time.time()
        start_time = last_time
        last_time_written = 0
        buffer = file_info.get_remain()
        file_size = file_info.size
        written = 0
        path = f'{self._dir}/{file_info.filename}'
        if os.path.exists(path):
            path = self._uniquify(path)

        error = False

        with open(path, "wb") as raw_file:
            while True:
                raw_file.write(buffer)
                written += len(buffer)

                if written == file_size:
                    break

                try:
                    buffer = self._get_data(reader)
                    curr_time = time.time()

                    if curr_time - last_time >= 3:
                        sys.stdout.write(f"клиент {addr}, мгновенная скорость: {written - last_time_written / 3} "
                              f"байт/c, средняя скорость: {written / (curr_time - last_time)} байт/c\n")
                        last_time = curr_time
                        last_time_written = written

                except ConnectionError as e:
                    error = True
                    break

        if error:
            os.remove(path)
            sock.send(self._FAILURE)
            sys.stdout.write(f'клиент {addr}, was written {written} bytes, expected {file_size} bytes')
        else:
            sock.send(self._SUCCESS)
            curr_time = time.time()
            sys.stdout.write(f"клиент {addr}, мгновенная скорость: {written - last_time_written / 3} "
                  f"байт/c, средняя скорость: {written / (curr_time - start_time)} байт/c\n")
        sock.close()

    def run(self):
        self._receiver.listen()
        while True:
            sock, addr = self._receiver.accept()
            thread = Thread(target=self._handle_new_connection, args=(sock, addr))
            thread.start()


if __name__ == '__main__':
    app = ServerApp(1999)
    app.run()
