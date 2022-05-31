# Generated by Django 3.2 on 2022-05-31 11:43

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('chat', '0002_unreadchatroommessages'),
    ]

    operations = [
        migrations.AddField(
            model_name='privatechatroom',
            name='connected_users',
            field=models.ManyToManyField(blank=True, related_name='connected_users', to=settings.AUTH_USER_MODEL),
        ),
    ]
