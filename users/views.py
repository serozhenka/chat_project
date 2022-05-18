from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.urls.exceptions import NoReverseMatch

from .forms import RegisterForm, LoginForm, AccountUpdateForm
from .models import Account

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

    if request.method == "GET":
        try:
            owner = Account.objects.get(id=user_id)
        except Account.DoesNotExist:
            return redirect('home')

        return render(request, 'users/account.html', context={'owner': owner})

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
                accounts.append((account, False))

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
        print(form)
        print(request.POST)
        if form.is_valid():
            owner.image.delete(save=True)  # delete old image
            form.save()
            return redirect('account:view', user_id=user_id)

    context['form'] = form

    return render(request, 'users/account_edit.html', context=context)
