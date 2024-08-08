from django.contrib import admin

# Register your models here.
from notifications.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["recipient", "read", "__str__", "created_at"]
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
    actions = ["mark_read", "mark_new"]

    @admin.action(description="Mark selected notifications as read")
    def mark_read(self, request, queryset):
        updated = queryset.update(read=True)
        if updated == 1:
            self.message_user(request, f"{updated} notification was marked as read.")
        else:
            self.message_user(request, f"{updated} notifications were marked as read.")

    @admin.action(description="Mark selected notifications as new")
    def mark_new(self, request, queryset):
        updated = queryset.update(read=False)
        if updated == 1:
            self.message_user(request, f"{updated} notification was marked as new.")
        else:
            self.message_user(request, f"{updated} notifications were marked as new.")
