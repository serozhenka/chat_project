from django.contrib import admin
from django.urls import path
from . import views

app_name = 'account'

urlpatterns = [
    path('<str:user_id>/', views.account_page, name='view'),
    path('<str:user_id>/edit/', views.account_edit, name='edit'),
]





