import json
from enum import Enum
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth import get_user_model
from django.contrib.humanize.templatetags.humanize import naturalday
from django.utils import timezone
from datetime import datetime

Account = get_user_model()


class MsgType(int, Enum):
    STANDARD = 0  # standard messages
    ERROR = 1  # error messages


class PublicChatConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        """
        Sent to the application when the client initially opens a
        connection and is about to finish the WebSocket handshake.
        """
        print("public chat connect" + str(self.scope['user']))

        await self.accept()
        await self.channel_layer.group_add("public_chatroom_1", self.channel_name)

    async def disconnect(self, code):
        """
        Sent to the application when either connection to the client is lost,
        either from the client closing the connection, the server closing the connection, or loss of the socket.
        """
        await self.close(code=code)

    async def receive_json(self, content, **kwargs):
        print(f"receive json: {content=}")
        command = content.get('command', None)
        if command == "send":
            try:
                if content['message'] == "fuck":
                    raise ClientError(422, "You are not allowed to cuss")
                await self.channel_layer.group_send(
                    "public_chatroom_1",
                    {
                        "type": "chat.message",
                        "msg_type": MsgType.STANDARD,
                        "image": self.scope['user'].image.url,
                        "username": self.scope['user'].username,
                        "user_id": self.scope['user'].id,
                        "message": content['message'],
                    }
                )
            except ClientError as e:
                e.__dict__.update({'msg_type': MsgType.ERROR})
                await self.send_json(e.__dict__)

    async def chat_message(self, event):
        timestamp = calculate_timestamp(timezone.now())
        await self.send_json({
            "msg_type": event.get('msg_type'),
            "image": event.get('image'),
            "username": event.get('username'),
            "user_id": event.get('user_id'),
            "message": event.get('message').strip(),
            "natural_timestamp": timestamp,
        })


class ClientError(Exception):

    def __init__(self, code, message=None):
        super().__init__()
        self.code = code
        self.message = message


def calculate_timestamp(timestamp):
    # today or yesterday
    if naturalday(timestamp) in ["today", "yesterday"]:
        str_time = datetime.strftime(timestamp, "%I:%M %p")
        ts = f'{naturalday(timestamp)} at {str_time}'
    else:
        ts = datetime.strftime(timestamp, "%m/%d/%Y")
    return str(ts)
