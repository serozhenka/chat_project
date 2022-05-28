from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
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
            self.friends.add(account)

            self.notifications.create(
                target=self.user,
                sender=account,
                redirect_url=f"{settings.BASE_URL}/account/{account.id}",
                message=f"You are now friends with {account.username}",
                content_type=ContentType.objects.get_for_model(self),
            )

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

        # notification for removee
        self.notifications.create(
            target=removee,
            sender=self.user,
            redirect_url=f"{settings.BASE_URL}/account/{self.user.id}/",
            message=f"You are no longer friends with {self.user.username}",
            content_type=ContentType.objects.get_for_model(self),
        )

        # notification for remover
        self.notifications.create(
            target=self.user,
            sender=removee,
            redirect_url=f"{settings.BASE_URL}/account/{removee.id}/",
            message=f"You are no longer friends with {removee.username}",
            content_type=ContentType.objects.get_for_model(self),
        )




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

        content_type = ContentType.objects.get_for_model(self)

        receiver_fl, _ = FriendList.objects.get_or_create(user=self.receiver)
        receiver_fl.add_friend(self.sender)

        # update receiver notification
        receiver_notification = Notification.objects.get(
            target=self.receiver,
            content_type=content_type,
            object_id=self.id
        )
        receiver_notification.redirect_url = f"{settings.BASE_URL}/account/{self.sender.id}"
        receiver_notification.message = f"You accepted {self.sender.username}'s friend request"
        receiver_notification.timestamp = timezone.now()
        receiver_notification.save()

        sender_fl, _ = FriendList.objects.get_or_create(user=self.sender)
        sender_fl.add_friend(self.receiver)

        # create notification for sender
        self.notifications.create(
            target=self.sender,
            sender=self.receiver,
            redirect_url=f"{settings.BASE_URL}/account/{self.receiver.id}/",
            message=f"{self.receiver.username} accepted your friend request",
            content_type=ContentType.objects.get_for_model(self),
        )

        self.is_active = False
        self.save()
        return receiver_notification

    def decline(self):
        """
        Decline friend request from receiver
            - update sender's and receiver's friend lists
        """

        # update receiver notification
        content_type = ContentType.objects.get_for_model(self)
        receiver_notification = Notification.objects.get(
            target=self.receiver,
            content_type=content_type,
            object_id=self.id
        )
        receiver_notification.redirect_url = f"{settings.BASE_URL}/account/{self.sender.id}"
        receiver_notification.message = f"You declined {self.sender.username}'s friend request"
        receiver_notification.timestamp = timezone.now()
        receiver_notification.save()

        # create notification for sender
        self.notifications.create(
            target=self.sender,
            sender=self.receiver,
            redirect_url=f"{settings.BASE_URL}/account/{self.receiver.id}/",
            message=f"{self.receiver.username} declined your friend request",
            content_type=ContentType.objects.get_for_model(self),
        )

        self.is_active = False
        self.save()
        return receiver_notification

    def cancel(self):
        """
        Cancel friend request sent by sender
            - update sender's and receiver's friend lists
        """
        content_type = ContentType.objects.get_for_model(self)

        # create notification for sender
        self.notifications.create(
            target=self.sender,
            sender=self.receiver,
            redirect_url=f"{settings.BASE_URL}/account/{self.receiver.id}/",
            message=f"You cancelled your friend request to {self.receiver.username}",
            content_type=ContentType.objects.get_for_model(self),
        )

        self.is_active = False
        self.save()

@receiver(post_save, sender=FriendRequest)
def create_notification(sender, instance, created, **kwargs):
    if created:
        instance.notifications.create(
            target=instance.receiver,
            sender=instance.sender,
            redirect_url=f"{settings.BASE_URL}/account/{instance.sender.id}",
            message=f"{instance.sender.username} sent you a friend request",
            content_type=instance
        )