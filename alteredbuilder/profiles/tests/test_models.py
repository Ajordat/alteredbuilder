from django.contrib.auth.models import User
from django.test import TestCase

from profiles.models import Follow


class ProfilesModelsTestCase(TestCase):
    """Test case focusing on the Models."""

    def test_to_string(self):
        """Test the string representations of all models."""
        follower_user = User.objects.create_user("follower_user")
        followed_user = User.objects.create_user("followed_user")
        follow = Follow.objects.create(follower=follower_user, followed=followed_user)

        self.assertEqual(str(follow), f"{follower_user} follows {followed_user}")
