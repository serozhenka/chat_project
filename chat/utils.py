from .models import PrivateChatRoom
from django.contrib.humanize.templatetags.humanize import naturalday
from datetime import datetime

def get_or_create_private_chat(user1, user2):
    try:
        chat = PrivateChatRoom.objects.get(user1=user1, user2=user2)
    except PrivateChatRoom.DoesNotExist:
        try:
            chat = PrivateChatRoom.objects.get(user1=user2, user2=user1)
        except PrivateChatRoom.DoesNotExist:
            chat = PrivateChatRoom.objects.create(user1=user1, user2=user2)
    return chat

def calculate_timestamp(timestamp):
    # today or yesterday
    if naturalday(timestamp) in ["today", "yesterday"]:
        str_time = datetime.strftime(timestamp, "%I:%M %p")
        ts = f'{naturalday(timestamp)} at {str_time}'
    else:
        ts = datetime.strftime(timestamp, "%m/%d/%Y")
    return str(ts)