from django.urls import path
from . import views

app_name = "friend"

urlpatterns = [
    path('friend_request/<str:receiver_id>/', views.send_friend_request, name='friend-request'),
    path('friend_request_list/', views.friend_requests, name='friend-request-list'),
]