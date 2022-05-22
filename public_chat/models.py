from django.db import models
from django.conf import settings

class PublicChatRoom(models.Model):
    title = models.CharField(max_length=255, unique=True)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True)

    def __str__(self):
        return self.title

    def connect_user(self, user):
        if user not in self.users.all():
            self.users.add(user)

    def disconnect_user(self, user):
        if user in self.users.all():
            self.users.remove(user)

    @property
    def group_name(self):
        """
        returns channels group name which sockets should subscribe to
        """
        return f"publicChatRoom-{self.id}"

class PublicChatRoomMessageManager(models.Manager):

    def by_room(self, room):
        return self.model.objects.filter(room=room).order_by('-timestamp')


class PublicChatRoomMessage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    room = models.ForeignKey(PublicChatRoom, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    content = models.TextField(blank=False)

    objects = PublicChatRoomMessageManager()

    def __str__(self):
        return self.content[0:50]


