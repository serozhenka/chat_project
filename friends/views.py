import json

from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from users.models import Account
from .models import FriendRequest

@login_required(login_url='login')
def friend_requests(request):
    friend_request_list = FriendRequest.objects.filter(receiver=request.user, is_active=True)
    return render(request, 'friends/friend_requests.html', context={'friend_requests': friend_request_list})

def send_friend_request(request, receiver_id):
    user = request.user
    payload = {}

    if request.method == "POST" and user.is_authenticated:
        try:
            receiver = Account.objects.get(id=receiver_id)
        except Account.DoesNotExist:
            return HttpResponse(json.dumps({'response': 'invalid receiver id'}), content_type='application/json')

        friend_request, _ = FriendRequest.objects.get_or_create(sender=user, receiver=receiver)
        if not friend_request.is_active:
            friend_request.is_active = True
            friend_request.save()
        payload['response'] = 'request sent'

    if not user.is_authenticated:
        payload['response'] = 'You are not authenticated'

    return HttpResponse(json.dumps(payload), content_type='application/json')

