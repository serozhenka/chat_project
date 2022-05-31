import json

from datetime import datetime
from enum import Enum
from django.conf import settings
from django.core.paginator import Paginator
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.contenttypes.models import ContentType

from chat.models import UnreadChatRoomMessages
from friends.models import FriendRequest, FriendList
from notifications.models import Notification
from notifications.utils import LazyNotificationEncoder
from chat.exceptions import ClientError

DEFAULT_NOTIFICATION_PAGE_SIZE = 5

class NotificationType(str, Enum):
	GENERAL_NOTIFICATION = "general"
	NEW_GENERAL_NOTIFICATION = "new_general"
	UPDATED_NOTIFICATION = "updated"
	PAGINATION_EXHAUSTED = "pagination_exhausted"
	REFRESH_GENERAL_NOTIFICATIONS = "refresh_general"
	UNREAD_GENERAL_COUNT = "general_count"
	CHAT_NOTIFICATION = "chat"

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
				payload = json.loads(payload)
				if len(payload) > 0:
					await self.send_general_notification_payload(payload['notifications'], payload['new_page_number'])
				else:
					await self.general_pagination_exhausted()
					# raise ClientError(204, "Something went wrong retrieving notifications")
			elif command == "accept_friend_request":
				payload = await self.accept_friend_request(self.scope['user'], content.get("notification_id"))
				if payload:
					payload = json.loads(payload)
					await self.send_updated_friend_request_notification(payload['notification'])
				else:
					raise ClientError(204, "An error occurred, try to refresh the browser")
			elif command == "decline_friend_request":
				payload = await self.decline_friend_request(self.scope['user'], content.get("notification_id"))
				if payload:
					payload = json.loads(payload)
					await self.send_updated_friend_request_notification(payload['notification'])
				else:
					raise ClientError(204, "An error occurred, try to refresh the browser")
			elif command == "refresh_general_notifications":
				payload = await self.refresh_general_notifications(
					self.scope['user'],
					content.get('oldest_timestamp'),
					content.get('newest_timestamp'),
				)
				if len(payload) > 0:
					payload = json.loads(payload)
					await self.send_refreshed_general_notifications(payload['notifications'])
				else:
					raise ClientError(204, "An error occurred, try to refresh the browser")
			elif command == "get_new_general_notifications":
				payload = await self.get_new_general_notifications(self.scope['user'], content.get('newest_timestamp'))
				if len(payload) > 0:
					payload = json.loads(payload)
					await self.send_new_general_notifications_payload(payload['notifications'])
				else:
					raise ClientError(204, "An error occurred, try to refresh the browser")
			elif command == "get_unread_general_notifications_count":
				payload = await self.get_unread_general_notifications_count(self.scope['user'])
				if len(payload) > 0:
					payload = json.loads(payload)
					await self.send_unread_general_notifications_count(payload['count'])
				else:
					raise ClientError(204, "An error occurred, try to refresh the browser")
			elif command == "mark_notifications_as_read":
				await self.mark_notifications_read(self.scope['user'])
			elif command == "get_chat_notifications":
				payload = await self.get_chat_notifications(self.scope['user'], content.get('page_number'))
				print(payload)
				if len(payload) > 0:
					payload = json.loads(payload)
					await self.send_chat_notifications(payload['notifications'], payload['new_page_number'])

		except ClientError as e:
			...

	async def display_progress_bar(self, display):
		print("NotificationConsumer: display_progress_bar: " + str(display))
		await self.send_json({
			"progress_bar": display,
		})

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

			paginator = Paginator(notifications, DEFAULT_NOTIFICATION_PAGE_SIZE)
			payload = {}

			if int(page_number) <= paginator.num_pages:
				s = LazyNotificationEncoder()
				serialized = s.serialize(paginator.page(page_number).object_list)
				payload['notifications'] = serialized
				payload['new_page_number'] = int(page_number) + 1
		else:
			raise ClientError(204, "User must be authenticated to receive notifications")

		return json.dumps(payload)

	async def send_updated_friend_request_notification(self, notification):
		await self.send_json({
			'notification_type': NotificationType.UPDATED_NOTIFICATION,
			'notification': notification,
		})

	@database_sync_to_async
	def accept_friend_request(self, user, notification_id):
		payload = {}
		if user.is_authenticated:
			try:
				notification = Notification.objects.get(id=notification_id)
				friend_request = notification.content_object
				if friend_request.receiver == user:
					updated_notification = friend_request.accept()
					s = LazyNotificationEncoder()
					payload['notification'] = s.serialize([updated_notification])[0]
					return json.dumps(payload)

			except Notification.DoesNotExist:
				raise ClientError(422, "An error occurred, try to refresh the browser")

	@database_sync_to_async
	def decline_friend_request(self, user, notification_id):
		payload = {}
		if user.is_authenticated:
			try:
				notification = Notification.objects.get(id=notification_id)
				friend_request = notification.content_object
				if friend_request.receiver == user:
					updated_notification = friend_request.decline()
					s = LazyNotificationEncoder()
					payload['notification'] = s.serialize([updated_notification])[0]
					return json.dumps(payload)

			except Notification.DoesNotExist:
				raise ClientError(422, "An error occurred, try to refresh the browser")

	async def general_pagination_exhausted(self):
		await self.send_json({
			'notification_type': NotificationType.PAGINATION_EXHAUSTED,
		})

	@database_sync_to_async
	def refresh_general_notifications(self, user, oldest_timestamp, newest_timestamp):
		payload = {}
		if user.is_authenticated:
			oldest_ts = datetime.strptime(oldest_timestamp[0:oldest_timestamp.find("+")], "%Y-%m-%d %H:%M:%S.%f")
			newest_ts = datetime.strptime(newest_timestamp[0:newest_timestamp.find("+")], "%Y-%m-%d %H:%M:%S.%f")

			friend_request_ct = ContentType.objects.get_for_model(FriendRequest)
			friend_list_ct = ContentType.objects.get_for_model(FriendList)

			notifications = Notification.objects.filter(
				target=user,
				content_type__in=[friend_request_ct, friend_list_ct],
				timestamp__gte=oldest_ts,
				timestamp__lte=newest_ts,
			).order_by('-timestamp')

			s = LazyNotificationEncoder()
			payload['notifications'] = s.serialize(notifications)
		else:
			raise ClientError(204, "User must be authenticated to get notifications")
		return json.dumps(payload)

	async def send_refreshed_general_notifications(self, notifications):
		await self.send_json({
			'notification_type': 'refresh_general',
			'notifications': notifications,
		})

	@database_sync_to_async
	def get_new_general_notifications(self, user, newest_timestamp):
		payload = {}
		if user.is_authenticated:
			newest_ts = datetime.strptime(newest_timestamp[0:newest_timestamp.find("+")], "%Y-%m-%d %H:%M:%S.%f")

			friend_request_ct = ContentType.objects.get_for_model(FriendRequest)
			friend_list_ct = ContentType.objects.get_for_model(FriendList)

			notifications = Notification.objects.filter(
				target=user,
				content_type__in=[friend_request_ct, friend_list_ct],
				timestamp__gt=newest_ts,
				is_read=False,
			).order_by('-timestamp')

			s = LazyNotificationEncoder()
			payload['notifications'] = s.serialize(notifications)
		else:
			raise ClientError(204, "User must be authenticated to get notifications")

		return json.dumps(payload)

	async def send_new_general_notifications_payload(self, notifications):
		await self.send_json({
			'notification_type': NotificationType.NEW_GENERAL_NOTIFICATION,
			'notifications': notifications,
		})

	@database_sync_to_async
	def get_unread_general_notifications_count(self, user):
		payload = {}
		if user.is_authenticated:
			friend_request_ct = ContentType.objects.get_for_model(FriendRequest)
			friend_list_ct = ContentType.objects.get_for_model(FriendList)

			notifications_count = Notification.objects.filter(
				target=user,
				content_type__in=[friend_request_ct, friend_list_ct],
				is_read=False,
			).count()
			payload['count'] = notifications_count
		else:
			raise ClientError(204, "User must be authenticated to get notifications")

		return json.dumps(payload)

	async def send_unread_general_notifications_count(self, notifications_count):
		await self.send_json({
			'notification_type': NotificationType.UNREAD_GENERAL_COUNT,
			'count': notifications_count,
		})

	@database_sync_to_async
	def mark_notifications_read(self, user):
		if user.is_authenticated:
			notifications = Notification.objects.filter(target=user)
			for notification in notifications:
				notification.is_read = True
				notification.save()

	@database_sync_to_async
	def get_chat_notifications(self, user, page_number):
		if user.is_authenticated:
			chat_messages_ct = ContentType.objects.get_for_model(UnreadChatRoomMessages)
			notifications = Notification.objects.filter(
				target=user,
				content_type=chat_messages_ct,
			).order_by('-timestamp')

			paginator = Paginator(notifications, DEFAULT_NOTIFICATION_PAGE_SIZE)
			payload = {}
			if int(page_number) <= paginator.num_pages:
				s = LazyNotificationEncoder()
				serialized_notifications = s.serialize(paginator.page(page_number).object_list)
				new_page_number = int(page_number)
				payload['notifications'] = serialized_notifications
				payload['new_page_number'] = new_page_number
		else:
			raise ClientError(204, "User must be authenticated to get notifications")

		return json.dumps(payload)

	async def send_chat_notifications(self, notifications, new_page_number):
		await self.send_json({
			'notification_type': NotificationType.CHAT_NOTIFICATION,
			'notifications': notifications,
			'new_page_number': new_page_number,
		})