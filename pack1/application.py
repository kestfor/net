import time
import uuid
from datetime import datetime, timedelta
from time import sleep

from pack1.message import Message
from pack1.receiver import Receiver
from pack1.sender import Sender


class Application:
    _time_out_to_die = 3

    def __init__(self, address: str, port: int):
        self.address = address
        self.port = port
        self.uuid = uuid.uuid4().int

        self._ids = {}
        self._receiver = Receiver(self.address, port)
        self._sender = Sender(self.address, port)

    def _is_alive(self, time_now: datetime, last_time: datetime) -> bool:
        if abs((time_now - last_time).total_seconds()) > self._time_out_to_die:
            return False
        else:
            return True

    def _check_group(self):

        now = datetime.now()

        changed = False
        for uuid, timestamp in self._ids.copy().items():
            if not self._is_alive(now, datetime.fromisoformat(timestamp)):
                changed = True

                address = self._ids[uuid]['address']
                self._ids.pop(uuid)
                print(f'{address} left group, last message time: {timestamp}')

        if changed:
            print(f'alive ips: {self._get_alive_ips()}')

    def _get_alive_ips(self) -> set:
        ips = set()
        for v in self._ids.values():
            ips.add(v['address'])
        return ips

    def check_messages(self):
        self._sender.send(Message(self.uuid, datetime.now().isoformat()))

        data, sender = self._receiver.receive()

        while data is not None:

            if data.uuid == self.uuid:
                data, sender = self._receiver.receive()
                continue

            if data is not None:
                address = sender[0]

                if data.uuid not in self._ids:
                    self._ids[data.uuid] = {"time": data.timestamp, "address": address}
                    print(f'{address} joined group at {data.timestamp}')
                    print(f'alive ips: {self._get_alive_ips()}')

                else:
                    self._ids[data.uuid]["time"] = data.timestamp

            data, sender = self._receiver.receive()


    def application_work(self):
        sleep(0.5)

    def start(self):

        while True:
            self.check_messages()
            self.application_work()

