import json
from enum import Enum
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.serializers import serialize
from django.utils import timezone

from .models import PrivateChatRoom, PrivateChatRoomMessage
from friends.models import FriendList
from users.utils import LazyAccountEncoder
from .exceptions import ClientError
from chat.utils import calculate_timestamp

class MsgType(str, Enum):
    STANDARD = "standard"  # standard messages
    # ERROR = 1  # error messages
    # PAYLOAD = 2
    # PROGRESS_BAR = 3
    ERROR = "error"
    JOIN = "join"
    GET_USER_INFO = "get_user_info"

class PrivateChatConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        # let everyone connect. But limit read/write to authenticated users
        await self.accept()

        # the room_id will define what it means to be "connected". If it is not None, then the user is connected.
        self.room_id = None

    async def receive_json(self, content, **kwargs):
        """
        Called when we get a text frame. Channels will JSON-decode the payload
        for us and pass it as the first argument.
        """
        # Messages will have a "command" key we can switch on
        command = content.get("command", None)
        try:
            if command == "join":
                await self.join_room(content.get("room_id"))
            elif command == "leave":
                await self.leave_room(content.get('room_id'))
            elif command == "send":
                room_id = content.get('room_id')
                if content['message'] == "fuck":
                    raise ClientError(422, "You are not allowed to cuss")

                if str(room_id) == str(self.room_id):
                    room = await self.get_room_or_error(self.scope['user'], self.room_id)

                    message = await self.create_private_room_chat_message(
                        user=self.scope['user'],
                        room=room,
                        message=content['message']
                    )

                    await self.channel_layer.group_send(
                        room.group_name,
                        {
                            'type': 'chat.message',
                            'image': self.scope['user'].image.url,
                            'username': self.scope['user'].username,
                            'user_id': self.scope['user'].id,
                            'message': content.get('message'),
                            "msg_id": message.id,
                        }
                    )

                else:
                    raise ClientError("Room Access Denied", "You do not have permissions to send message to this room")
            elif command == "get_room_chat_messages":
                pass
            elif command == "get_user_info":
                print(content, content.get("room_id"))
                room = await self.get_room_or_error(self.scope['user'], content.get('room_id'))
                payload = await self.get_user_info(self.scope['user'], room)
                if payload:
                    payload = json.loads(payload)
                    await self.send_json({
                        "msg_type": MsgType.GET_USER_INFO,
                        "user_info": payload['user_info']
                    })
                else:
                    raise ClientError(422, "Something went wrong retrieving user details")
        except ClientError as e:
            await self.handle_client_error(e)

    async def disconnect(self, code):
        """
        Called when the WebSocket closes for any reason.
        """
        if self.room_id: await self.leave_room(self.room_id)

    async def join_room(self, room_id):
        """
        Called by receive_json when someone sent a join command.
        """
        # The logged-in user is in our scope thanks to the authentication ASGI middleware (AuthMiddlewareStack)
        print("ChatConsumer: join_room: " + str(room_id))
        try:
            room = await self.get_room_or_error(self.scope['user'], room_id)
            self.room_id = room.id
        except ClientError as e:
            return await self.handle_client_error(e)

        await self.channel_layer.group_add(
            room.group_name,
            self.channel_name
        )

        await self.send_json({
            'msg_type': MsgType.JOIN,
            'room_id': room_id,
        })

    async def leave_room(self, room_id):
        """
        Called by receive_json when someone sent a leave command.
        """
        room = await self.get_room_or_error(self.scope['user'], room_id)
        self.room_id = None

        await self.channel_layer.group_discard(
            room.group_name,
            self.channel_name
        )

        print("ChatConsumer: leave_room")

    async def send_room(self, room_id, message):
        """
        Called by receive_json when someone sends a message to a room.
        """
        print("ChatConsumer: send_room")

        # These helper methods are named by the types we send - so chat.join becomes chat_join

    async def chat_join(self, event):
        """
        Called when someone has joined our chat.
        """
        # Send a message down to the client
        print("ChatConsumer: chat_join: " + str(self.scope["user"].id))

    async def chat_leave(self, event):
        """
        Called when someone has left our chat.
        """
        # Send a message down to the client
        print("ChatConsumer: chat_leave")

    async def chat_message(self, event):
        """
        Called when someone has messaged our chat.
        """
        timestamp = calculate_timestamp(timezone.now())
        await self.send_json({
            'msg_type': MsgType.STANDARD,
            'image': event.get('image'),
            'username': event.get('username'),
            'user_id': event.get('user_id'),
            'message': event.get('message'),
            'natural_timestamp': timestamp,
            "msg_id": event.get('msg_id'),
        })
        print("ChatConsumer: chat_message")

    async def send_messages_payload(self, messages, new_page_number):
        """
        Send a payload of messages to the ui
        """
        print("ChatConsumer: send_messages_payload. ")

    async def send_user_info_payload(self, user_info):
        """
        Send a payload of user information to the ui
        """
        print("ChatConsumer: send_user_info_payload. ")

    async def display_progress_bar(self, is_displayed):
        """
        1. is_displayed = True
            - Display the progress bar on UI
        2. is_displayed = False
            - Hide the progress bar on UI
        """
        print("DISPLAY PROGRESS BAR: " + str(is_displayed))

    @database_sync_to_async
    def get_room_or_error(self, user, room_id):
        """
        Getting the private chat room for the user and
        also checking that user has perms
        """
        try:
            room = PrivateChatRoom.objects.get(id=room_id)
        except PrivateChatRoom.DoesNotExist:
            # TODO
            raise ClientError(422, "private chat room does not exist")

        if user not in [room.user1, room.user2]:
            raise ClientError(422, "You do not have permission to join this room")

        friend_list = FriendList.objects.get(user=user).friends.all()
        if not any(x in friend_list for x in [room.user1, room.user2]):
            raise ClientError(422, "Must be friends to chat")

        return room

    @database_sync_to_async
    def get_user_info(self, user, room):
        """
        Retrieve info for the user the authenticated user chats with
        """
        try:
            other_user = room.user1 if room.user1 != user else room.user2
            payload = {}
            s = LazyAccountEncoder()
            payload['user_info'] = s.serialize([other_user])[0]
            return json.dumps(payload)
        except ClientError as e:
            print(e)
        return None

    async def handle_client_error(self, e):
        e.__dict__.update({'msg_type': MsgType.ERROR})
        await self.send_json(e.__dict__)

    @database_sync_to_async
    def create_private_room_chat_message(self, room, user, message):
        return PrivateChatRoomMessage.objects.create(user=user, room=room, content=message)


