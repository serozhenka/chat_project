import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth import get_user_model

Account = get_user_model()

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
            await self.channel_layer.group_send(
                "public_chatroom_1",
                {
                    "type": "chat.message",
                    "image": self.scope['user'].image.url,
                    "username": self.scope['user'].username,
                    "user_id": self.scope['user'].id,
                    "message": content['message'],
                }
            )

    async def chat_message(self, event):
        print(f"chat_message from: {event['user_id']}")
        await self.send_json({
            "image": event.get('image'),
            "username": event.get('username'),
            "user_id": event.get('user_id'),
            "message": event.get('message').strip(),
        })




