from django.contrib import admin

# Register your models here.
from notifications.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["recipient", "__str__", "created_at"]
    list_filter = ["read"]
    search_fields = ["recipient__username", "verb"]
    readonly_fields = [
        "verb",
        "recipient",
        "actor",
        "content_type",
        "object_id",
        "read",
    ]
