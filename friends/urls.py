from django.urls import path
from . import views

app_name = "friend"

urlpatterns = [
    path('remove/<str:friend_id>/', views.remove_friend, name='friend-remove'),

    path('friend_request/<str:receiver_id>/', views.send_friend_request, name='friend-request'),
    path('friend_request_list/', views.friend_requests, name='friend-request-list'),
    path('friend_request/<str:friend_request_id>/accept/', views.accept_friend_request, name='friend-request-accept'),
    path('friend_request/<str:friend_request_id>/decline/', views.decline_friend_request, name='friend-request-decline'),
]