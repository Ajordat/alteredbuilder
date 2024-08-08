from notifications.models import Notification


def add_notifications(request):
    context = {}

    if request.user.is_authenticated:
        context["notifications"] = Notification.objects.filter(
            recipient=request.user
        ).select_related("actor").prefetch_related("content_object", "content_object__deck")
        
        context["has_unread_notifications"] = context["notifications"].filter(read=False).exists()

    return context
