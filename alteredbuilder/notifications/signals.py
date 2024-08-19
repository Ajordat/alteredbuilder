from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models.signals import post_delete, post_save, pre_delete
from django.dispatch import receiver

from decks.models import Comment, Deck, LovePoint
from notifications.models import Notification, NotificationType
from profiles.models import Follow


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
            Notification.objects.update_or_create(
                recipient=recipient,
                verb=NotificationType.LOVE,
                content_type=ContentType.objects.get_for_model(instance.deck),
                object_id=instance.deck.id,
                defaults={"read": False},
            )


@receiver(post_delete, sender=LovePoint)
def delete_love_notification(sender, instance: LovePoint, **kwargs):
    def consider_delete_notification():
        try:
            notification = Notification.objects.get(
                recipient=instance.deck.owner,
                verb=NotificationType.LOVE,
                content_type=ContentType.objects.get_for_model(instance.deck),
                object_id=instance.deck.id,
            )

            if notification.content_object.love_count == 0:
                notification.delete()
        except (Notification.DoesNotExist, Deck.DoesNotExist):
            pass

    transaction.on_commit(consider_delete_notification)


@receiver(post_save, sender=Deck)
def create_deck_notification(sender, instance: Deck, created, **kwargs):
    content_type = ContentType.objects.get_for_model(instance)
    creator = instance.owner
    if created and instance.is_public:
        follows = Follow.objects.filter(followed=creator)
        notifications = []

        for follow in follows:
            notifications.append(
                Notification(
                    recipient=follow.follower,
                    verb=NotificationType.DECK,
                    actor=creator,
                    content_type=content_type,
                    object_id=instance.id,
                )
            )
        Notification.objects.bulk_create(notifications)
    elif not instance.is_public:
        # This is useful for the case where a user makes their Deck private. I'd prefer
        # it if it wasn't needed to perform a db operation every time, but it seems to
        # be the fastest way right now
        # https://medium.com/@mmzeynalli/how-to-detect-field-changes-in-django-ae4bc719aea2
        Notification.objects.filter(content_type=content_type, object_id=instance.id).exclude(recipient=creator).delete()


@receiver(pre_delete, sender=Deck)
def delete_deck_notification(sender, instance: Deck, **kwargs):
    Notification.objects.filter(
        content_type=ContentType.objects.get_for_model(instance),
        object_id=instance.id,
    ).delete()
