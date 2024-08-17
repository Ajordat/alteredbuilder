from django.contrib.auth.models import User
from django.test import TestCase

from profiles.models import UserProfile


class ProfilesSignalsTestCase(TestCase):
    """Test case focusing on the signals."""

    def test_signal_trigger(self):
        """Test the string representations of all models."""
        user = User.objects.create_user("test_user")
        user.refresh_from_db()

        self.assertIsNotNone(user.profile)
        try:
            UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:  # pragma: no cover
            self.fail("UserProfile was not created")
