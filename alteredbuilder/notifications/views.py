from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, get_object_or_404

from notifications.models import Notification, NotificationType


@login_required
def notification_detail(request: HttpRequest, pk: int) -> HttpResponse:
    """View to view the content of a Notification. The Notification is marked as read
    and the user is redirected to the content_object's view.

    Args:
        request (HttpRequest): The request.
        pk (int): The ID of the Notification.

    Raises:
        Http404: If the Notification is not found. This can happen if the request is
                 crafted.

    Returns:
        HttpResponse: A redirection to the Notification's content view.
    """
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)

    match notification.verb:
        case NotificationType.COMMENT | NotificationType.LOVE | NotificationType.DECK:
            redirect_url = notification.content_object.get_absolute_url()
            Notification.objects.filter(
                recipient=request.user,
                content_type=notification.content_type,
                object_id=notification.object_id,
            ).update(read=True)
        case _:
            raise Http404("Notification does not exist")

    return redirect(redirect_url)
