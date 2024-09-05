import json
import uuid
import datetime


class Message:

    def __init__(self, uuid: int, timestamp: str):
        self.uuid = uuid
        self.timestamp = timestamp


class MessageEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, Message):
            return obj.__dict__
        return json.JSONEncoder.default(self, obj)
