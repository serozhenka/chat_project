import json
from enum import Enum
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.humanize.templatetags.humanize import naturalday
from django.utils import timezone
from datetime import datetime
from .models import PublicChatRoom


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

        self.room_id = None
        await self.accept()
        await self.channel_layer.group_add("public_chatroom_1", self.channel_name)

    async def disconnect(self, code):
        """
        Sent to the application when either connection to the client is lost,
        either from the client closing the connection, the server closing the connection, or loss of the socket.
        """
        try:
            if self.room_id:
                await self.leave_room(self.room_id)
        except ClientError as e:
            pass
            # await self.handle_client_error(e)

        await self.close(code=code)

    async def receive_json(self, content, **kwargs):
        print(f"receive json: {content=}")
        command = content.get('command', None)

        try:
            if command == "send":
                if content['message'] == "fuck":
                    raise ClientError(422, "You are not allowed to cuss")
                room_id = content.get('room_id')

                if str(room_id) == str(self.room_id):
                    room = await self.get_room_or_exception(self.room_id)
                    await self.channel_layer.group_send(
                        room.group_name,
                        {
                            "type": "chat.message",
                            "msg_type": MsgType.STANDARD,
                            "image": self.scope['user'].image.url,
                            "username": self.scope['user'].username,
                            "user_id": self.scope['user'].id,
                            "message": content['message'],
                        }
                    )
                else:
                    raise ClientError(
                        "Access Denied",
                        "You are not allowed to send message to the group you are not member of"
                    )

            elif command == "join":
                await self.join_room(content.get('room_id'))
            elif command == "leave":
                await self.leave_room(content.get('room_id'))

        except ClientError as e:
            await self.handle_client_error(e)

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

    async def join_room(self, room_id):
        """
        Called by receive_json when somebody sent "join" command
        """
        try:
            room = await self.get_room_or_exception(room_id)
            self.room_id = room.id
            await database_sync_to_async(room.connect_user)(self.scope['user'])
            await self.channel_layer.group_add(
                room.group_name,
                self.channel_name
            )
        except ClientError as e:
            await self.handle_client_error(e)

    async def leave_room(self, room_id):
        """
        Called by receive_json when somebody sent "leave" command
        """
        try:
            room = await self.get_room_or_exception(room_id)
            await database_sync_to_async(room.disconnect_user)(self.scope['user'])
            await self.channel_layer.group_discard(
                room.group_name,
                self.channel_name
            )
        except ClientError as e:
            await self.handle_client_error(e)

    @database_sync_to_async
    def get_room_or_exception(self, room_id):
        try:
            room = PublicChatRoom.objects.get(pk=room_id)
            return room
        except PublicChatRoom.DoesNotExist:
            raise ClientError("Room Invalid", "Public Chat Room with that id does not exist")

    async def handle_client_error(self, e):
        e.__dict__.update({'msg_type': MsgType.ERROR})
        await self.send_json(e.__dict__)


class ClientError(Exception):

    def __init__(self, code, message):
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
