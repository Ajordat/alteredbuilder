from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext as _


class NotificationType(models.TextChoices):
    COMMENT = "comment"


class Notification(models.Model):
    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    verb = models.CharField(choices=NotificationType.choices)
    actor = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications_sent"
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveBigIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    def __str__(self) -> str:
        match self.verb:
            case NotificationType.COMMENT:
                return _("%(actor)s commented on deck '%(deck_name)s'") % {
                    "actor": self.actor.username,
                    "deck_name": self.content_object.deck.name,
                }
            case _:
                return _("New notification by %(actor)s") % {
                    "actor": self.actor.username
                }
