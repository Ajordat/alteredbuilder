from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from django.dispatch import receiver

from decks.models import Comment
from notifications.models import Notification, NotificationType


@receiver(post_save, sender=Comment)
def create_comment_notification(sender, instance: Comment, created: bool, **kwargs):
    if created:
        deck = instance.deck
        recipient = deck.owner

        if recipient != instance.user:
            Notification.objects.create(
                recipient=recipient,
                verb=NotificationType.COMMENT,
                actor=instance.user,
                content_type=ContentType.objects.get_for_model(instance),
                object_id=instance.id,
            )
