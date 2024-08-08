from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse

from notifications.models import Notification, NotificationType


def notification_detail(request, pk: int):
    try:
        notification = Notification.objects.get(pk=pk, recipient=request.user)
        match notification.verb:
            case NotificationType.COMMENT:
                notification.read = True
                notification.save()
                return redirect(
                    reverse(
                        "deck-detail",
                        kwargs={"pk": notification.content_object.deck.id},
                    )
                )
    except Notification.DoesNotExist:
        raise Http404("Notification does not exist")
