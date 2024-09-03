from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from profiles.models import UserProfile


User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created: bool, **kwargs):
    """Signal that triggers after saving a User object.

    When a User is created, create the corresponding Profile.

    Args:
        sender (Type[User]): The User class.
        instance (User): The User object that triggered the signal.
        created (bool): If the object was just created or simply saved.
    """

    if created:
        UserProfile.objects.create(user=instance)
