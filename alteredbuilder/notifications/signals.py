from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from django.dispatch import receiver

from decks.models import Comment
from notifications.models import Notification, NotificationType


@receiver(post_save, sender=Comment)
def create_comment_notification(sender, comment: Comment, created: bool, **kwargs):
    if created:
        deck = comment.deck
        recipient = deck.owner

        if recipient != comment.user:
            Notification.objects.create(
                recipient=recipient,
                verb=NotificationType.COMMENT,
                actor=comment.user,
                content_type=ContentType.objects.get_for_model(comment),
                object_id=comment.id,
            )
