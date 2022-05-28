from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

class Notification(models.Model):
    # user which receives the notification
    target = models.ForeignKey(settings.AUTH_USER_MODEL, models.CASCADE, related_name='target')

    # user which triggered the notification
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, models.CASCADE, related_name='notification_sender', null=True, blank=True)
    
    redirect_url = models.URLField(max_length=256, null=True, blank=True)
    
    # statement describing the notification
    message = models.CharField(max_length=255, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()

    def __str__(self):
        return self.message

    def get_content_object_type(self):
        return self.content_object.get_cname

