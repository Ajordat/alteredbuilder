from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext as _, ngettext


class NotificationType(models.TextChoices):
    COMMENT = "comment"
    DECK = "deck"
    FOLLOW = "follow"
    LOVE = "love"


class Notification(models.Model):
    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    verb = models.CharField(choices=NotificationType.choices)
    actor = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications_sent", null=True
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveBigIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    created_at = models.DateTimeField(auto_now=True)
    read = models.BooleanField(default=False)

    def __str__(self) -> str:
        if not self.content_object:
            return _("New notification")

        match self.verb:
            case NotificationType.COMMENT:
                return _("%(actor)s commented on deck '%(deck_name)s'") % {
                    "actor": self.actor.username,
                    "deck_name": self.content_object.name,
                }
            case NotificationType.LOVE:
                return ngettext(
                    "%(love_count)s user liked your deck '%(deck_name)s'",
                    "%(love_count)s users liked your deck '%(deck_name)s'",
                    self.content_object.love_count,
                ) % {
                    "love_count": self.content_object.love_count,
                    "deck_name": self.content_object.name,
                }
            case NotificationType.DECK:
                return _("%(actor)s created deck '%(deck_name)s'") % {
                    "actor": self.actor.username,
                    "deck_name": self.content_object.name,
                }
            case NotificationType.FOLLOW:
                return _("%(actor)s started following you") % {"actor": self.actor}
            case _:
                return _("New notification")

    def get_absolute_url(self):
        return reverse("notification-detail", kwargs={"pk": self.pk})

    class Meta:
        ordering = ["-created_at"]
