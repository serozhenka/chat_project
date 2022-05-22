from django.shortcuts import render
from django.conf import settings

def home_page(request):
    context = {
        'debug_mode': settings.DEBUG,
        'room_id': 1,
    }
    return render(request, 'home/home.html', context=context)
