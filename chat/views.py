from django.shortcuts import render
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from .models import PrivateChatRoom, PrivateChatRoomMessage

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
