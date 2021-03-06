from django.urls import path
from . import views

app_name = "chat"

urlpatterns = [
    path('', views.private_chat_view, name='private-chat-room'),
    path('get_private_chat/', views.get_private_chat, name='get-private-chat'),
]