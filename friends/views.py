import json

from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from users.models import Account
from .models import FriendRequest, FriendList

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


def accept_friend_request(request, friend_request_id):
    payload = {}
    user = request.user

    if request.method == "POST" and user.is_authenticated:
        try:
            friend_request = FriendRequest.objects.get(id=friend_request_id)
            if friend_request.receiver == user:
                friend_request.accept()
                payload['response'] = 'request accepted'
                return HttpResponse(json.dumps(payload), content_type='application/json')
        except FriendRequest.DoesNotExist:
            pass

        return HttpResponse(json.dumps({'response': 'Not able to process such a request'}), content_type='application/json')


def decline_friend_request(request, friend_request_id):
    payload = {}
    user = request.user

    if request.method == "POST" and user.is_authenticated:
        try:
            friend_request = FriendRequest.objects.get(id=friend_request_id)
            if friend_request.receiver == user:
                friend_request.decline()
                payload['response'] = 'request declined'
                return HttpResponse(json.dumps(payload), content_type='application/json')
        except FriendRequest.DoesNotExist:
            pass

        return HttpResponse(json.dumps({'response': 'Not able to process such a request'}), content_type='application/json')


def remove_friend(request, friend_id):
    payload = {}
    user = request.user

    if request.method == "POST" and user.is_authenticated:
        try:
            removee = Account.objects.get(pk=friend_id)
            friend_list = FriendList.objects.get(user=user)
            friend_list.unfriend(removee)
            payload['response'] = 'removed'
        except Account.DoesNotExist:
            return HttpResponse(json.dumps({'response': 'unable to remove unexisting user'}), content_type='application/json')

    return HttpResponse(json.dumps(payload), content_type='application/json')
