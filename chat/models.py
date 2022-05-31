from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from notifications.models import Notification


class PrivateChatRoom(models.Model):
    user1 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user1')
    user2 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user2')
    connected_users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='connected_users')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.user1.username}-{self.user2.username}'

    @property
    def group_name(self):
        return f"private_chat_room_{self.id}"

    def connect_user(self, user):
        if user not in self.connected_users.all():
            self.connected_users.add(user)

    def disconnect_user(self, user):
        if user in self.connected_users.all():
            self.connected_users.remove(user)


class PrivateChatRoomMessageManager(models.Manager):
    def by_room(self, room):
        return PrivateChatRoomMessage.objects.filter(room=room).order_by('-timestamp')


class PrivateChatRoomMessage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    room = models.ForeignKey(PrivateChatRoom, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    objects = PrivateChatRoomMessageManager()

    def __str__(self):
        return f"{self.user.username}-{self.content[0:50]}"


class UnreadChatRoomMessages(models.Model):
    room = models.ForeignKey(PrivateChatRoom, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    count = models.IntegerField(default=0)
    # most_recent_message = models.ForeignKey(PrivateChatRoomMessage, on_delete=models.CASCADE)
    most_recent_message = models.CharField(max_length=500, blank=True, null=True)
    reset_timestamp = models.DateTimeField()
    notifications = GenericRelation(Notification)

    def __str__(self):
        return f"Messages that {self.user.username} hasn't read yet"

    def save(self, *args, **kwargs):
        if not self.id:
            self.reset_timestamp = timezone.now()
        return super(UnreadChatRoomMessages, self).save(*args, **kwargs)

    @property
    def get_cname(self):
        return "UnreadChaRoomMessages"

    def get_other_user(self):
        return self.room.user2 if self.room.user1 == self.user else self.room.user1


@receiver(post_save, sender=PrivateChatRoom)
def create_unread_chatroom_messages_obj(sender, instance, created, **kwargs):
    if created:
        UnreadChatRoomMessages.objects.create(room=instance, user=instance.user1)
        UnreadChatRoomMessages.objects.create(room=instance, user=instance.user2)

@receiver(pre_save, sender=UnreadChatRoomMessages)
def increment_unread_chatroom_messages_count(sender, instance, **kwargs):
    if instance.id:
        previous = UnreadChatRoomMessages(id=instance.id)
        if previous.count < instance.count:
            content_type = ContentType.objects.get_for_model(instance)
            other_user = instance.room.user2 if instance.room.user1 == instance.user else instance.room.user1
            try:
                notification = Notification.objects.get(
                    target=instance.user,
                    content_type=content_type,
                    object_id=instance.id,
                )
                notification.message = instance.most_recent_message
                notification.timestamp = timezone.now()
                notification.save()
            except Notification.DoesNotExist:
                instance.notifications.create(
                    target=instance.user,
                    sender=other_user,
                    redirect_url=f"{settings.BASE_URL}/chat/?room_id={instance.room.id}",
                    message=instance.most_recent_message,
                    content_type=content_type
                )

@receiver(pre_save, sender=UnreadChatRoomMessages)
def remove_unread_chatroom_messages_count(sender, instance, **kwargs):
    if instance.id:
        previous = UnreadChatRoomMessages(id=instance.id)
        if previous.count > instance.count:
            content_type = ContentType.objects.get_for_model(instance)
            try:
                notification = Notification.objects.get(
                    target=instance.user,
                    content_type=content_type,
                    object_id=instance.id,
                )
                notification.delete()
            except Notification.DoesNotExist:
                pass