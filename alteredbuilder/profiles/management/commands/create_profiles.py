from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from profiles.models import UserProfile


class Command(BaseCommand):
    help = "Create a profile for every user that does not have one."

    def handle(self, *args, **kwargs):
        User = get_user_model()
        users_without_profiles = User.objects.filter(profile__isnull=True)

        for user in users_without_profiles:
            UserProfile.objects.create(user=user)
            self.stdout.write(
                self.style.SUCCESS(f"Created profile for {user.username}")
            )

        self.stdout.write(
            self.style.SUCCESS("Finished creating profiles for all users.")
        )
