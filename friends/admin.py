from django.contrib import admin
from .models import FriendList, FriendRequest

class FriendListAdmin(admin.ModelAdmin):
    list_display = ('user', )
    list_filter = ('user', )
    search_fields = ('user', )

    class Meta:
        model = FriendList

class FriendRequestAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver')
    list_filter = ('sender', 'receiver')
    search_fields = ('sender__email', 'receiver__email')

    class Meta:
        model = FriendRequest

admin.site.register(FriendList, FriendListAdmin)
admin.site.register(FriendRequest, FriendRequestAdmin)
