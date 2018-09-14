from django.contrib import admin
from django.contrib.auth.models import User, Group

from .models import Account

# Register your models here.

admin.site.unregister(User)
admin.site.unregister(Group)

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ["contact", "active", "agent", "balance"]