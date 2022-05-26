import json
from enum import Enum
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.serializers import serialize

from .models import PrivateChatRoom, PrivateChatRoomMessage
from friends.models import FriendList
from users.utils import LazyAccountEncoder

class MsgType(str, Enum):
    # STANDARD = 0  # standard messages
    # ERROR = 1  # error messages
    # PAYLOAD = 2
    # PROGRESS_BAR = 3
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
                pass
            elif command == "send":
                pass
            elif command == "get_room_chat_messages":
                pass
            elif command == "get_user_info":
                print(content, content.get("room_id"))
                room = await self.get_room_or_error(self.scope['user'], content.get('room_id'))
                print(room)
                payload = await self.get_user_info(self.scope['user'], room)
                if payload:
                    payload = json.loads(payload)
                    await self.send_json({
                        "msg_type": MsgType.GET_USER_INFO,
                        "user_info": payload['user_info']
                    })
                else:
                    raise Exception("Something went wrong retrieving user details")
        except Exception as e:
            raise e

    async def disconnect(self, code):
        """
        Called when the WebSocket closes for any reason.
        """
        # Leave the room
        pass

    async def join_room(self, room_id):
        """
        Called by receive_json when someone sent a join command.
        """
        # The logged-in user is in our scope thanks to the authentication ASGI middleware (AuthMiddlewareStack)
        print("ChatConsumer: join_room: " + str(room_id))
        try:
            room = await self.get_room_or_error(self.scope['user'], room_id)
        except Exception as e:
            return
        await self.send_json({
            'msg_type': MsgType.JOIN,
            'room_id': room_id,
        })

    async def leave_room(self, room_id):
        """
        Called by receive_json when someone sent a leave command.
        """
        # The logged-in user is in our scope thanks to the authentication ASGI middleware
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
        # Send a message down to the client
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
            raise Exception("to do")

        if user not in [room.user1, room.user2]:
            raise Exception("You do not have permission to join this room")

        friend_list = FriendList.objects.get(user=user).friends.all()
        if not any(x in friend_list for x in [room.user1, room.user2]):
            raise Exception("Must be friends to chat")

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
        except Exception as e:
            print(e)
        return None


