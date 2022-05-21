from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Account

class AccountAdmin(admin.ModelAdmin):
    list_display = ('email', 'username', 'is_staff', 'is_superuser', 'joined')
    search_fields = ('email', 'username')
    readonly_fields = ('id', 'joined', 'last_login')

    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()

    class Meta:
        model = Account

admin.site.register(Account, AccountAdmin)
