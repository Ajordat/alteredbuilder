from django.http import HttpRequest

from notifications.models import Notification


def add_notifications(request: HttpRequest) -> dict:
    """Context processor that adds if there's any unread notification to the context.

    Args:
        request (HttpRequest): The HTTP request.

    Returns:
        dict: The context.
    """
    context = {}

    if request.user.is_authenticated:
        context["has_unread_notifications"] = Notification.objects.filter(
            recipient=request.user, read=False
        ).exists()

    return context
