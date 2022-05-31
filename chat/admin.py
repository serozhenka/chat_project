from django.contrib import admin
from django.core.paginator import Paginator
from django.core.cache import cache
from django.db import models
from .models import PrivateChatRoom, PrivateChatRoomMessage, UnreadChatRoomMessages


class CachingPaginator(Paginator):
    def _get_count(self):
        if not hasattr(self, "_count"):
            self._count = None

        if self._count is None:
            try:
                key = "adm:{0}:count".format(hash(self.object_list.query.__str__()))
                self._count = cache.get(key, -1)
                if self._count == -1:
                    self._count = super().count
                    cache.set(key, self._count, 3600)
            except:
                self._count = len(self.object_list)
        return self._count

    count = property(_get_count)

class PrivateChatRoomMessageAdmin(admin.ModelAdmin):
    list_display = ('room', 'user', 'timestamp')
    list_filter = ('room', 'user', 'timestamp')
    search_fields = ('room__title', 'user__username', 'timestamp')
    readonly_fields = ('id', 'timestamp')

    show_full_result_count = False
    paginator = CachingPaginator

    class Meta:
        model = PrivateChatRoomMessage

class PrivateChatRoomAdmin(admin.ModelAdmin):
    list_display = ('id', 'user1', 'user2')
    search_fields = ('id', 'user1__username', 'user1_email', 'user2__username', 'user2_email')
    readonly_fields = ('id',)

    class Meta:
        model = PrivateChatRoom

class UnreadChatRoomMessagesAdmin(admin.ModelAdmin):
    list_display = ['room', 'user', 'count']
    search_fields = ['room__user1__username', 'room__user2__username', ]
    readonly_fields = ('id',)

    class Meta:
        model = UnreadChatRoomMessages


admin.site.register(PrivateChatRoom, PrivateChatRoomAdmin)
admin.site.register(PrivateChatRoomMessage, PrivateChatRoomMessageAdmin)
admin.site.register(UnreadChatRoomMessages, UnreadChatRoomMessagesAdmin)
