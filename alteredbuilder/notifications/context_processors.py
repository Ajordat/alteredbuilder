from notifications.models import Notification


def add_notifications(request):
    context = {}

    if request.user.is_authenticated:
        context["has_unread_notifications"] = Notification.objects.filter(recipient=request.user, read=False).exists()

    return context
