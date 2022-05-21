import os
import cv2
import json
import base64
import requests

from django.http import HttpResponse
from django.core import files
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.urls.exceptions import NoReverseMatch
from django.core.files.storage import default_storage
from django.core.files.storage import FileSystemStorage

from .forms import RegisterForm, LoginForm, AccountUpdateForm
from .models import Account
from friends.models import FriendList, FriendRequest
from friends.utils import get_friend_request_or_false
from friends.friend_request_statuses import FriendRequestStatus

TEMP_PROFILE_IMAGE_NAME = "temp_profile_image.png"

def redirect_next_url(request):
    # function returning a redirect to next url
    # from form's post request which is a hidden input

    if request.method == "POST":
        destination = request.POST.get('next', 'home')
        try:
            return redirect(destination)
        except NoReverseMatch:
            pass

    return redirect('home')

def register_page(request):
    if request.user.is_authenticated:
        return redirect('home')

    context = {}

    if request.method == "GET":
        context['next_url'] = request.GET.get('next', None)
    elif request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect_next_url(request)
        else:
            context['registration_form'] = form

    return render(request, 'users/register.html', context=context)


def login_page(request):
    if request.user.is_authenticated:
        return redirect('home')

    context = {}
    if request.method == "GET":
        context['next_url'] = request.GET.get('next', None)
    elif request.method == "POST":
        form = LoginForm(request.POST)

        if form.is_valid():
            cleaned_form = form.cleaned_data
            user = authenticate(email=cleaned_form['email'], password=cleaned_form['password'])
            if user:
                login(request, user)
                return redirect_next_url(request)

        context['login_form'] = LoginForm(request.POST)

    return render(request, 'users/login.html', context=context)


@login_required(login_url='login')
def logout_page(request):
    logout(request)
    return redirect('home')


def account_page(request, user_id):
    """
    - Logic here is kind of tricky
        is_self
        is_friend
            -1: NO_REQUEST_SENT
            0: THEM_SENT_TO_YOU
            1: YOU_SENT_TO_THEM
    """
    context = {}

    if request.method == "GET":
        try:
            owner = Account.objects.get(id=user_id)
            friend_list = FriendList.objects.get(user=owner)
            friends = friend_list.friends.all()
            if friends.filter(pk=request.user.id).exists():
                is_friend = True
                request_sent = 0
            else:
                is_friend = False

                # Request from them to you: FriendRequestStatus.THEM_SENT_TO_YOU
                if friend_request := get_friend_request_or_false(sender=owner, receiver=request.user):
                    request_sent = FriendRequestStatus.THEM_SENT_TO_YOU.value
                    context['pending_friend_request_id'] = friend_request.id

                # Request from you to them: FriendRequestStatus.YOU_SENT_TO_THEM
                elif friend_request := get_friend_request_or_false(sender=request.user, receiver=owner):
                    request_sent = FriendRequestStatus.YOU_SENT_TO_THEM.value

                # No friend request hase been sent: FriendRequestStatus.NO_REQUEST_SENT
                else:
                    request_sent = FriendRequestStatus.NO_REQUEST_SENT.value

        except Account.DoesNotExist:
            return redirect('home')

        if request.user.is_authenticated:
            friend_requests = FriendRequest.objects.filter(receiver=request.user, is_active=True)
            context['friend_requests'] = friend_requests

        context.update({
            'owner': owner,
            'friends': friends,
            'request_sent': request_sent,
            'is_friend': is_friend,
        })
        return render(request, 'users/account.html', context=context)

def account_search_view(request):
    context = {}

    if request.method == "GET":
        search_query = request.GET.get('q', None)
        if search_query:
            search_results = Account.objects.filter(
                Q(email__icontains=search_query) |
                Q(username__icontains=search_query)
            )

            accounts = []
            for account in search_results:
                is_friend = account in FriendList.objects.get(user=request.user).friends.all()
                accounts.append((account, is_friend))

            context['accounts'] = accounts

    return render(request, 'users/account_results.html', context=context)


@login_required(login_url='login')
def account_edit(request, user_id):
    context = {}
    try:
        owner = Account.objects.get(id=user_id)
    except Account.DoesNotExist:
        return redirect('home')

    if owner != request.user:
        return redirect('home')

    if request.method == 'GET':
        form = AccountUpdateForm(instance=request.user)

    elif request.method == 'POST':
        form = AccountUpdateForm(request.POST, request.FILES, instance=request.user, request=request)
        if form.is_valid():
            # owner.image.delete(save=True)  # delete old image
            form.save()
            return redirect('account:view', user_id=user_id)

    context['form'] = form
    context['DATA_UPLOAD_MAX_MEMORY_SIZE'] = settings.DATA_UPLOAD_MAX_MEMORY_SIZE

    return render(request, 'users/account_edit.html', context=context)


@login_required(login_url='login')
def crop_image(request, user_id):
    payload = {}

    try:
        user = Account.objects.get(id=user_id)
    except Account.DoesNotExist:
        return redirect('home')

    if user != request.user:
        return redirect('home')

    if request.method == "POST" and user.is_authenticated:
        try:
            imageString = request.POST.get('image')
            url = save_temp_profile_image_from_base64String(imageString, user)
            img = cv2.imread(url)

            cropX = int(float(str(request.POST.get("cropX"))))
            cropY = int(float(str(request.POST.get("cropY"))))
            cropWidth = int(float(str(request.POST.get("cropWidth"))))
            cropHeight = int(float(str(request.POST.get("cropHeight"))))

            cropX = 0 if cropX < 0 else cropX
            cropY = 0 if cropY < 0 else cropY

            cropped_image = img[cropY:cropY + cropHeight, cropX:cropX + cropWidth]
            cv2.imwrite(url, cropped_image)
            user.image.delete()
            user.image.save("profile_image.png", files.File(open(url, 'rb')))
            user.save()

            payload['result'] = 'success'
            payload['cropped_image_url'] = user.image.url

            os.remove(url)
            if os.path.exists(f"{settings.TEMP}/{str(user.id)}"):
                os.rmdir(f"{settings.TEMP}/{str(user.id)}")

        except Exception as e:
            print(e)
            payload['result'] = 'error'
            payload['exception'] = str(e)

        return HttpResponse(json.dumps(payload), content_type='application/json')


def save_temp_profile_image_from_base64String(imageString, user):
    INCORRECT_PADDING_EXCEPTION = "Incorrect padding"

    try:
        if not os.path.exists(settings.TEMP):
            os.mkdir(settings.TEMP)

        if not os.path.exists(f"{settings.TEMP}/{str(user.id)}"):
            os.mkdir(f"{settings.TEMP}/{str(user.id)}")

        url = os.path.join(f"{settings.TEMP}/{str(user.id)}", TEMP_PROFILE_IMAGE_NAME)
        storage = FileSystemStorage(location=url)
        image = base64.b64decode(imageString)

        with storage.open("", 'wb+') as destination:
            destination.write(image)
            destination.close()

        return url

    except Exception as e:
        if str(e) == INCORRECT_PADDING_EXCEPTION:
            imageString += "=" * ((4 - len(imageString) % 4) % 4)
            return save_temp_profile_image_from_base64String(imageString, user)

    return None