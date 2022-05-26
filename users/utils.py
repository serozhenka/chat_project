from django.core.serializers.python import Serializer


class LazyAccountEncoder(Serializer):
    def get_dump_object(self, obj):
        dump_object = {
            'id': obj.id,
            'email': obj.email,
            'username': obj.username,
            'image': obj.image.url,
        }
        return dump_object