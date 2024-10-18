from http import HTTPStatus
from typing import Any

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.query import QuerySet
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.utils.timesince import timesince
from django.utils.translation import gettext_lazy as _
from django.views.generic.list import ListView

from api.utils import ajax_request, ApiJsonResponse
from notifications.models import Notification, NotificationType


class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification

    def get_queryset(self) -> QuerySet[Any]:
        qs = super().get_queryset()

        qs = qs.filter(recipient=self.request.user)

        return qs


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

    # Mark the Notification as read
    Notification.objects.filter(
        recipient=request.user,
        content_type=notification.content_type,
        object_id=notification.object_id,
    ).update(read=True)

    # Route the user to the relevant view
    return redirect(notification.content_object.get_absolute_url())


@ajax_request(methods=["GET"])
def fetch_notifications(request: HttpRequest) -> ApiJsonResponse:
    """View to fetch all notifications of a given user.

    Args:
        request (HttpRequest): The HTTP request.

    Returns:
        ApiJsonResponse: A JSON with all the user's notifications.
    """

    # If the User is not authenticated, return 401
    if not request.user.is_authenticated:
        return ApiJsonResponse("Unauthenticated", HTTPStatus.UNAUTHORIZED)

    notifications = Notification.objects.filter(
        recipient=request.user, read=False
    ).order_by("-created_at")[:10]

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


@login_required
def clear_notifications(request: HttpRequest) -> HttpResponse:
    """View to clear all notifications of a given user.

    Args:
        request (HttpRequest): The HTTP request.

    Returns:
        HttpResponse: A redirection to the current view (if clicked from the dropdown)
                      or the Notification's list view.
    """

    Notification.objects.filter(recipient=request.user, read=False).update(read=True)

    if next := request.GET.get("next"):
        return redirect(next)

    return redirect("notification-list")
