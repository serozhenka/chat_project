from django.core.serializers.python import Serializer
from django.contrib.humanize.templatetags.humanize import naturaltime


class LazyNotificationEncoder(Serializer):

    def get_dump_object(self, obj):
        dump_object = {
            'notification_type': str(obj.get_content_object_type()),
            'notification_id': str(obj.id),
            'message': obj.message,
            'is_read': obj.is_read,
            'natural_timestamp': str(naturaltime(obj.timestamp)),
            'timestamp': str(obj.timestamp),
            'actions': {
                'redirect_url': str(obj.redirect_url),
            },
            'sender': {
                'image': obj.sender.image.url,
            }
        }

        if obj.get_content_object_type() == "FriendRequest":
            dump_object['is_active'] = obj.content_object.is_active

        if obj.get_content_object_type() == "UnreadChatRoomMessages":
            dump_object['sender']['title'] = obj.content_object.get_other_user.username

        return dump_object