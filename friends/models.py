from django.db import models
from django.conf import settings
from django.utils import timezone

class FriendList(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user')
    friends = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='friends')

    def __str__(self):
        return self.user.username

    def add_friend(self, account):
        if account in self.friends.all():
            self.friends.add(account)

    def remove_friend(self, account):
        if account in self.friends.all():
            self.friends.remove(account)

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

    def __str__(self):
        return f"{self.sender.username}-{self.receiver.username}"

    def accept(self):
        """
        Accept friend request
            - update sender's and receiver's friend lists
        """

        receiver_fl, _ = FriendList.objects.get_or_create(user=self.receiver)
        receiver_fl.friends.add(self.sender)
        sender_fl, _ = FriendList.objects.get_or_create(user=self.sender)
        sender_fl.friends.add(self.receiver)
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