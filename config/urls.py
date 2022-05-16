from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as AuthenticationViews

from home.views import home_page
from users import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_page, name='home'),

    path('register/', auth_views.register_page, name='register'),
    path('login/', auth_views.login_page, name='login'),
    path('logout/', auth_views.logout_page, name='logout'),

    path('password_change/done/', AuthenticationViews.PasswordChangeDoneView.as_view(
        template_name='password_reset/password_change_done.html'),
        name='password_change_done'),

    path('password_change/', AuthenticationViews.PasswordChangeView.as_view(
        template_name='password_reset/password_change.html'),
        name='password_change'),

    path('password_reset/done/', AuthenticationViews.PasswordResetCompleteView.as_view(
        template_name='password_reset/password_reset_done.html'),
        name='password_reset_done'),

    path('reset/<uidb64>/<token>/', AuthenticationViews.PasswordResetConfirmView.as_view(),
         name='password_reset_confirm'),

    path('password_reset/', AuthenticationViews.PasswordResetView.as_view(template_name='password_reset/password_reset_form.html'), name='password_reset'),

    path('reset/done/', AuthenticationViews.PasswordResetCompleteView.as_view(
        template_name='password_reset/password_reset_complete.html'),
        name='password_reset_complete'),

    path('accounts/', include('users.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


