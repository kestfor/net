import time

from utils.Address import Address


class MsgToResend:
    def __init__(self, data: bytes, addr: Address):
        self.msg = data
        self.addr = addr
        self.time = time.time()