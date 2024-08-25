from http import HTTPStatus

from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.utils.timesince import timesince
from django.utils.translation import gettext_lazy as _

from api.utils import ajax_request, ApiJsonResponse
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

    if notification.verb not in NotificationType:
        raise Http404("Notification does not exist")

    Notification.objects.filter(
        recipient=request.user,
        content_type=notification.content_type,
        object_id=notification.object_id,
    ).update(read=True)

    return redirect(notification.content_object.get_absolute_url())


@login_required
@ajax_request(methods=["GET"])
def fetch_notifications(request: HttpRequest):
    notifications = Notification.objects.filter(recipient=request.user)[:10]

    data = []
    for notification in notifications:
        data.append(
            {
                "id": notification.pk,
                "message": str(notification),
                "read": notification.read,
                "timestamp": _("%(time_since)s ago")
                % {"time_since": timesince(notification.created_at)},
            }
        )

    return ApiJsonResponse({"notifications": data}, HTTPStatus.OK)
