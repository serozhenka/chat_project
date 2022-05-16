from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from home.views import home_page
from users import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_page, name='home'),

    path('register/', auth_views.register_page, name='register'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


