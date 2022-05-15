from django.contrib import admin
from .models import Account

class AccountAdmin(admin.ModelAdmin):
    list_display = ('email', 'username', 'is_staff', 'is_superuser', 'joined')
    search_fields = ('email', 'username')
    readonly_fields = ('id', 'joined', 'last_login')

    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()

admin.site.register(Account, AccountAdmin)
