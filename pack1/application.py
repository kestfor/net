import threading
import time
import uuid
from datetime import datetime
from time import sleep

from message import Message
from receiver import Receiver
from sender import Sender


class Application:
    _time_out_to_die = 3
    _time_out_to_send = 1

    def __init__(self, address: str, port: int):
        self.address = address
        self.port = port
        self.Uuid = uuid.uuid4().int

        self._ids = {}
        self._receiver = Receiver(self.address, port)
        self._sender = Sender(self.address, port)

    def _is_alive(self, time_now: datetime, last_time: datetime) -> bool:
        if abs((time_now - last_time).total_seconds()) > self._time_out_to_die:
            return False
        else:
            return True

    def update_group(self):

        now = datetime.now()

        changed = False
        for Uuid, dictionary in self._ids.copy().items():
            if not self._is_alive(now, datetime.fromisoformat(dictionary['time'])):
                changed = True

                address = dictionary['address']
                self._ids.pop(Uuid)
                print(f'{address} left group, last message time: {dictionary["time"]}')

        if changed:
            alive = self._get_alive_ips()
            print(f'alive ips: {alive}' if len(alive) > 0 else 'there is no alive copy now')

    def _get_alive_ips(self) -> set:
        ips = set()
        for v in self._ids.values():
            ips.add(v['address'])
        return ips

    def check_messages(self):
        while True:
            self._sender.send(Message(self.Uuid))

            data, sender = self._receiver.receive()

            while data is not None:

                if data.Uuid == self.Uuid:
                    data, sender = self._receiver.receive()
                    continue

                if data is not None:

                    address = sender[0]
                    now = datetime.now().isoformat()

                    if data.Uuid not in self._ids:
                        self._ids[data.Uuid] = {"time": now, "address": address}
                        print(f'{address} joined group at {now}')
                        print(f'alive ips: {self._get_alive_ips()}')
                        print(f'amount {len(self._ids) + 1}')

                    else:
                        self._ids[data.Uuid]["time"] = now

                data, sender = self._receiver.receive()

            self.update_group()
            time.sleep(self._time_out_to_send)

    def close(self):
        self._receiver.close()
        self._sender.close()

    def application_work(self):
        while True:
            sleep(0.5)

    def start(self):
        t1 = threading.Thread(target=self.check_messages)

        t1.daemon = True
        t1.start()

        self.application_work()
