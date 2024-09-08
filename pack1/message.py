import json


class Message:

    def __init__(self, uuid: int):
        self.Uuid = uuid


class MessageEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, Message):
            return obj.__dict__
        return json.JSONEncoder.default(self, obj)
