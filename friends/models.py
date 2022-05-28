from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericRelation
from chat.utils import get_or_create_private_chat
from notifications.models import Notification

class FriendList(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user')
    friends = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='friends')
    notifications = GenericRelation(Notification)

    @property
    def get_cname(self):
        return self.__class__.__name__

    def __str__(self):
        return self.user.username

    def add_friend(self, account):
        if account in self.friends.all():
            print(1)
            self.friends.add(account)

            chat = get_or_create_private_chat(user1=self.user, user2=account)
            chat.is_active = True
            chat.save()

    def remove_friend(self, account):
        if account in self.friends.all():
            self.friends.remove(account)

            chat = get_or_create_private_chat(user1=self.user, user2=account)
            chat.is_active = False
            chat.save()

    def unfriend(self, removee):
        # remove a friend from person list that terminates a friendship
        remover = self
        remover.remove_friend(removee)

        # remove remover from removee friend list
        removee_fl = FriendList.objects.get(user=removee)
        removee_fl.remove_friend(self.user)

    def is_mutual_friends(self, friend):
        if friend in self.friends.all():
            return True
        return False


class FriendRequest(models.Model):
    """
    Friend request consists of:
        1. Sender
        2. Receiver
    """

    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sender")
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="receiver")
    is_active = models.BooleanField(blank=True, null=False, default=True)
    created = models.DateTimeField(auto_now_add=True)
    notifications = GenericRelation(Notification)

    @property
    def get_cname(self):
        return self.__class__.__name__

    def __str__(self):
        return f"{self.sender.username}-{self.receiver.username}"

    def accept(self):
        """
        Accept friend request
            - update sender's and receiver's friend lists
        """

        receiver_fl, _ = FriendList.objects.get_or_create(user=self.receiver)
        receiver_fl.add_friend(self.sender)
        sender_fl, _ = FriendList.objects.get_or_create(user=self.sender)
        sender_fl.add_friend(self.receiver)
        self.is_active = False
        self.save()

    def decline(self):
        """
        Decline friend request from receiver
            - update sender's and receiver's friend lists
        """
        self.is_active = False
        self.save()

    def cancel(self):
        """
        Cancel friend request sent by sender
            - update sender's and receiver's friend lists
        """
        self.is_active = False
        self.save()