from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from profiles.models import UserProfile


class Command(BaseCommand):
    help = "Create a profile for every user that does not have one."

    def handle(self, *args, **kwargs):
        User = get_user_model()
        users_without_profiles = User.objects.filter(profile__isnull=True)

        profiles = []
        for user in users_without_profiles:
            profiles.append(UserProfile(user=user))

        UserProfile.objects.bulk_create(profiles)

        self.stdout.write(
            self.style.SUCCESS("Finished creating profiles for all users.")
        )
