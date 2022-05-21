from django.db.models.signals import post_save
from django.dispatch import receiver
from friends.models import FriendList
from .models import Account

@receiver(post_save, sender=Account)
def friend_list_create(sender, instance, created, **kwargs):
    if created:
        FriendList.objects.create(user=instance)