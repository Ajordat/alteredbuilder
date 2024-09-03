from typing import Type

from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models.signals import post_delete, post_save, pre_delete
from django.dispatch import receiver

from decks.models import Comment, Deck, LovePoint
from notifications.models import Notification, NotificationType
from profiles.models import Follow


@receiver(post_save, sender=Comment)
def create_comment_notification(
    sender: Type[Comment], instance: Comment, created: bool, **kwargs
):
    """Signal that triggers after saving a Comment object.

    When a User Comments on a Deck, create a Notification to all Users who had
    previously Commented on the Deck.

    Args:
        sender (Type[Comment]): The Comment class.
        instance (Comment): The Comment object that triggered the signal.
        created (bool): If the object was just created or simply saved.
    """
    if created:
        deck = instance.deck
        content_type = ContentType.objects.get_for_model(deck)

        # Retrieve all users that Commented in a Deck
        users = list(deck.comments.values_list("user__id", flat=True))
        # Add the owner of the Deck
        users.append(deck.owner.id)
        # Make it unique
        users = list(set(users))
        # Remove the creator of the Comment
        users.remove(instance.user.id)

        # Create a Notification to each of the users
        for user in users:
            Notification.objects.create(
                recipient_id=user,
                verb=NotificationType.COMMENT,
                actor=instance.user,
                content_type=content_type,
                object_id=deck.id,
            )


@receiver(post_save, sender=Follow)
def create_follow_notifications(
    sender: Type[Follow], instance: Follow, created: bool, **kwargs
):
    """Signal that triggers after saving a Follow object.

    When a User starts Following another User, create a Notification for the affected
    User.

    Args:
        sender (Type[Follow]): The Follow class.
        instance (Follow): The Follow object that triggered the signal.
        created (bool): If the object was just created or simply saved.
    """
    if created:
        follower = instance.follower
        Notification.objects.create(
            recipient=instance.followed,
            verb=NotificationType.FOLLOW,
            actor=follower,
            content_type=ContentType.objects.get_for_model(follower.profile),
            object_id=follower.profile.id,
        )


@receiver(pre_delete, sender=Follow)
def delete_follow_notification(sender: Type[Follow], instance: Follow, **kwargs):
    """Signal that triggers before deleting a Follow object.

    When a User starts stops Following another User, delete the Notification that
    informed about the original Follow action.

    Args:
        sender (Type[Follow]): The Follow class.
        instance (Follow): The Follow object that triggered the signal.
    """
    profile = instance.follower.profile
    Notification.objects.filter(
        content_type=ContentType.objects.get_for_model(profile),
        object_id=profile.id,
    ).delete()


@receiver(post_save, sender=LovePoint)
def create_love_notification(
    sender: Type[LovePoint], instance: LovePoint, created: bool, **kwargs
):
    """Signal that triggers after saving a LovePoint object.

    When a User Loves a Deck, create a Notification for the Deck's creator. If it
    already exists, the status will be changed to unread and the update date will be
    moved to now.

    Args:
        sender (Type[LovePoint]): The LovePoint class.
        instance (LovePoint): The LovePoint object that triggered the signal.
        created (bool): If the object was just created or simply saved.
    """
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
def delete_love_notification(sender: Type[LovePoint], instance: LovePoint, **kwargs):
    """Signal that triggers after deleting a LovePoint object.

    When a User removes a LovePoint from a Deck, delete the Notification unless the
    Deck is still Loved by other Users. That is done to avoid a User spamming the
    creator of the Deck, and since Love-related Notifications are aggregated (multiple
    Users liking the same Deck only generates one Notification) it's undesired to
    delete the Notification.

    The evaluation of the Deck's love points is done after the all the related
    operations are complete. This is done because this signal needs to be independent
    of the delete operation individual actions and has to trigger once it is all done.

    What happens is that deleting a LovePoint also requires subtracting the amount of
    love from the Deck itself. Which this signal is dependant from. Hence the whole
    delete operation needs to happen inside a transaction and this signal needs to run
    after that.

    Args:
        sender (Type[LovePoint]): The LovePoint class.
        instance (LovePoint): The LovePoint object that triggered the signal.
    """

    def consider_delete_notification():
        try:
            notification = Notification.objects.get(
                recipient=instance.deck.owner,
                verb=NotificationType.LOVE,
                content_type=ContentType.objects.get_for_model(instance.deck),
                object_id=instance.deck.id,
            )

            # If the Deck's love count is 0, the Notification is not reporting anything
            # useful hence it needs to be removed
            if notification.content_object.love_count == 0:
                notification.delete()
        except (Notification.DoesNotExist, Deck.DoesNotExist):
            pass

    transaction.on_commit(consider_delete_notification)


@receiver(post_save, sender=Deck)
def create_deck_notification(sender: Type[Deck], instance: Deck, created, **kwargs):
    """Signal that triggers after saving a Deck object.

    When a User creates a Deck, if it's public create a Notification for all the
    creator's followers.

    Args:
        sender (Type[Deck]): The Deck class.
        instance (Deck): The Deck object that triggered the signal.
    """
    content_type = ContentType.objects.get_for_model(instance)
    creator = instance.owner
    if created and instance.is_public:
        follows = Follow.objects.filter(followed=creator)
        notifications = []

        # Create a Notification for each follower
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
        Notification.objects.filter(
            content_type=content_type, object_id=instance.id
        ).exclude(recipient=creator).delete()


@receiver(pre_delete, sender=Deck)
def delete_deck_notification(sender: Type[Deck], instance: Deck, **kwargs):
    """Signal that triggers before deleting a Deck object.

    When a User deletes a Deck, delete any related Notifications.

    Args:
        sender (Type[Deck]): The Deck class.
        instance (Deck): The Deck object that triggered the signal.
    """
    Notification.objects.filter(
        content_type=ContentType.objects.get_for_model(instance),
        object_id=instance.id,
    ).delete()
