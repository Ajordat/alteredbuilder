from django.http import Http404
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse

from notifications.models import Notification, NotificationType


def notification_detail(request, pk: int):
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)

    match notification.verb:
        case NotificationType.COMMENT | NotificationType.LOVE:
            redirect_url = reverse(
                "deck-detail", kwargs={"pk": notification.content_object.id}
            )
            Notification.objects.filter(
                recipient=request.user,
                content_type=notification.content_type,
                object_id=notification.object_id,
            ).update(read=True)
        case _:
            raise Http404("Notification does not exist")

    return redirect(redirect_url)
