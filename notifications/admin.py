from django.contrib import admin
from .models import Notification


class NotificationAdmin(admin.ModelAdmin):
    list_display = ['content_type', 'timestamp']
    list_filter = ['target', 'content_type', 'timestamp']
    search_fields = ['target__username', 'target__email']

admin.site.register(Notification, NotificationAdmin)
