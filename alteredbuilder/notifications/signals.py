from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from decks.models import Comment, LovePoint
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
                content_type=ContentType.objects.get_for_model(deck),
                object_id=deck.id,
            )


@receiver(post_save, sender=LovePoint)
def create_love_notification(sender, instance: LovePoint, created: bool, **kwargs):
    if created:
        recipient = instance.deck.owner
        if recipient != instance.user:
            notification, _ = Notification.objects.get_or_create(
                recipient=recipient,
                verb=NotificationType.LOVE,
                content_type=ContentType.objects.get_for_model(instance.deck),
                object_id=instance.deck.id,
            )
            notification.read = False
            notification.save()


@receiver(post_delete, sender=LovePoint)
def delete_love_notification(sender, instance: LovePoint, **kwargs):
    try:
        notification = Notification.objects.get(
            recipient=instance.deck.owner,
            verb=NotificationType.LOVE,
            object_id=instance.deck.id,
        )
        if notification.content_object.love_count == 0:
            notification.delete()
    except Notification.DoesNotExist:
        pass
