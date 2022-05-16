from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.urls.exceptions import NoReverseMatch
from .forms import RegisterForm

def register_page(request):
    if request.user.is_authenticated:
        return redirect('home')

    context = {}

    if request.method == "GET":
        context['next_url'] = request.GET.get('next', None)
    elif request.method == "POST":
        form = RegisterForm(request.POST)
        destination = request.POST.get('next', 'home')
        if form.is_valid():
            user = form.save()
            login(request, user)
            try:
                return redirect(destination)
            except NoReverseMatch:
                return redirect('home')
        else:
            context['registration_form'] = form

    return render(request, 'users/register.html', context=context)


