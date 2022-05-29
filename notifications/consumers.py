import json

from enum import Enum
from django.conf import settings
from django.core.paginator import Paginator
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.contenttypes.models import ContentType

from friends.models import FriendRequest, FriendList
from notifications.models import Notification
from notifications.utils import LazyNotificationEncoder
# from notifications.constants import *
from chat.exceptions import ClientError

DEFAULT_CHAT_NOTIFICATION_PAGE_SIZE = 5

class NotificationType(str, Enum):
	GENERAL_NOTIFICATION = "general"

class NotificationConsumer(AsyncJsonWebsocketConsumer):
	"""
	Passing data to and from header.html. Notifications are displayed as "drop-downs" in the nav bar.
	There is two major categories of notifications:
		1. General Notifications
			1. FriendRequest
			2. FriendList
		1. Chat Notifications
			1. UnreadChatRoomMessages
	"""

	async def connect(self):
		"""
		Called when the websocket is handshaking as part of initial connection.
		"""
		print("NotificationConsumer: connect: " + str(self.scope["user"]))
		await self.accept()

	async def disconnect(self, code):
		"""
		Called when the WebSocket closes for any reason.
		"""
		print("NotificationConsumer: disconnect")

	async def receive_json(self, content, **kwargs):
		"""
		Called when we get a text frame. Channels will JSON-decode the payload
		for us and pass it as the first argument.
		"""
		command = content.get("command", None)
		print("NotificationConsumer: receive_json. Command: " + command)
		try:
			if command == "general_notification":
				payload = await self.get_general_notifications(self.scope['user'], content.get('new_page_number'))
				print(payload)
				if payload:
					payload = json.loads(payload)
					await self.send_general_notification_payload(payload['notifications'], payload['new_page_number'])
				else:
					raise ClientError(204, "Something went wrong retrieving notifications")
		except ClientError as e:
			...

	async def display_progress_bar(self, display):
		print("NotificationConsumer: display_progress_bar: " + str(display))
		await self.send_json(
			{
				"progress_bar": display,
			},
		)

	async def send_general_notification_payload(self, notifications, new_page_number):
		await self.send_json({
			'notification_type': NotificationType.GENERAL_NOTIFICATION,
			'notifications': notifications,
			'new_page_number': new_page_number,
		})

	@database_sync_to_async
	def get_general_notifications(self, user, page_number):
		"""
			Get General Notifications with Pagination (next page of results).
			This is for appending to the bottom of the notifications list.
			General Notifications are:
				1. FriendRequest
				2. FriendList
		"""
		if user.is_authenticated:
			friend_request_ct = ContentType.objects.get_for_model(FriendRequest)
			friend_list_ct = ContentType.objects.get_for_model(FriendList)
			notifications = Notification.objects.filter(
				target=user,
				content_type__in=[friend_request_ct, friend_list_ct]
			).order_by('-timestamp')

			paginator = Paginator(notifications, DEFAULT_CHAT_NOTIFICATION_PAGE_SIZE)
			payload = {}

			if int(page_number) <= paginator.num_pages:
				s = LazyNotificationEncoder()
				serialized = s.serialize(paginator.page(page_number).object_list)
				payload['notifications'] = serialized
				payload['new_page_number'] = int(page_number) + 1
		else:
			raise ClientError(204, "User must be authenticated to receive notifications")

		return json.dumps(payload)
