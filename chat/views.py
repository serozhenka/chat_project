import json

from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from .models import PrivateChatRoom, PrivateChatRoomMessage
from .utils import get_or_create_private_chat
from users.models import Account

@login_required(login_url='login')
def private_chat_view(request):
    user = request.user

    # rooms authenticated user is the part of
    rooms = PrivateChatRoom.objects.filter((Q(user1=user) | Q(user2=user)), Q(is_active=True)).distinct()

    # m_and_f structure (messages and friends)
    # [{"message": msg, "friend": friend}, ...]
    # message represents last written message in chat
    m_and_f = []
    for room in rooms:
        friend = room.user1 if room.user2 == user else room.user2
        m_and_f.append({
            "message": "",
            "friend": friend,
        })

    return render(request, 'chat/room.html', context={
        'm_and_f': m_and_f,
        'debug': settings.DEBUG,
    })

def get_private_chat(request):
    user1 = request.user
    payload = {}
    if request.method == "POST":
        if user1.is_authenticated:
            user2_id = request.POST.get("user_id")
            try:
                user2 = Account.objects.get(id=user2_id)
                chat = get_or_create_private_chat(user1=user1, user2=user2)
                payload['response'] = 'success'
                payload['room_id'] = chat.id
            except Account.DoesNotExist:
                payload['response'] = 'error'
        return HttpResponse(json.dumps(payload), content_type="application/json")
