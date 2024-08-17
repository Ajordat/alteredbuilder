from http import HTTPStatus

from django.contrib.auth.models import User
from django.db.models import Count
from django.test import TestCase
from django.urls import reverse

from profiles.models import Follow
from profiles.views import ProfileListView


class ProfilesListViewTestCase(TestCase):
    """Test case focusing on the signals."""

    @classmethod
    def setUpTestData(cls):
        """Create the database data for this test.

        Specifically, it creates:
        * 4 Users
        * 6 Follow
        """
        user1 = User.objects.create_user("user1")
        user2 = User.objects.create_user("user2")
        user3 = User.objects.create_user("user3")
        user4 = User.objects.create_user("user4")
        Follow.objects.create(follower=user1, followed=user2)
        Follow.objects.create(follower=user1, followed=user3)
        Follow.objects.create(follower=user1, followed=user4)
        Follow.objects.create(follower=user2, followed=user3)
        Follow.objects.create(follower=user2, followed=user4)
        Follow.objects.create(follower=user3, followed=user4)

    def test_view(self):
        response = self.client.get(reverse("profile-list"))

        most_followed_users = (
            User.objects.annotate(follower_count=Count("followers"))
            .filter(follower_count__gt=0)
            .order_by("-follower_count")[: ProfileListView.USER_COUNT_DISPLAY]
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "profiles/userprofile_list.html")
        self.assertQuerySetEqual(
            most_followed_users, response.context["most_followed_users"], ordered=True
        )
