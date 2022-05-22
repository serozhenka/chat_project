from django.contrib import admin
from django.core.paginator import Paginator
from django.core.cache import cache
from django.db import models
from .models import PublicChatRoom, PublicChatRoomMessage


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

class PublicChatRoomMessageAdmin(admin.ModelAdmin):
    list_display = ('room', 'user', 'timestamp')
    list_filter = ('room', 'user', 'timestamp')
    search_fields = ('room__title', 'user__username', 'timestamp')
    readonly_fields = ('id', 'room', 'user', 'timestamp')

    show_full_result_count = False
    paginator = CachingPaginator

    class Meta:
        model = PublicChatRoomMessage

class PublicChatRoomAdmin(admin.ModelAdmin):
    list_display = ('id', 'title')
    search_fields = ('id', 'title')
    readonly_fields = ('id',)

    class Meta:
        model = PublicChatRoom


admin.site.register(PublicChatRoom, PublicChatRoomAdmin)
admin.site.register(PublicChatRoomMessage, PublicChatRoomMessageAdmin)