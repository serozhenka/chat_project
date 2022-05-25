from django.db import models
from django.conf import settings

class PrivateChatRoom(models.Model):
    user1 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user1')
    user2 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user2')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.user1.username}-{self.user2.username}'

    @property
    def group_name(self):
        return f"private_chat_room_{self.id}"


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