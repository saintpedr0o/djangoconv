from django.contrib import admin
from .models import UserAPIKey


@admin.register(UserAPIKey)
class UserAPIKeyAdmin(admin.ModelAdmin):
    list_display = ("user", "key", "created_at", "updated_at")
    search_fields = ("user__username", "user__email", "key")
    readonly_fields = ("key", "created_at", "updated_at")
