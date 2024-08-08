from notifications.models import Notification


def add_notifications(request):
    if request.user.is_authenticated:
        notifications = Notification.objects.filter(
            recipient=request.user
        ).select_related("actor")[:5]
    else:
        notifications = None

    return {"notifications": notifications}
