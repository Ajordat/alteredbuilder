from notifications.models import Notification


def add_notifications(request):
    context = {}

    if request.user.is_authenticated:
        notifications = Notification.objects.filter(
            recipient=request.user
        ).select_related("actor").prefetch_related("content_object", "content_object__deck")
        
        context["has_unread_notifications"] = notifications.filter(read=False).exists()
        context["notifications"] = notifications[:10]

    return context
