from django.urls import path
from . import views

urlpatterns = [
    path('', views.private_chat_view, name='private-chat-room'),
]