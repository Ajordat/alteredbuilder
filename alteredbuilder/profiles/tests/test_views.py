from http import HTTPStatus
from uuid import uuid4

from django.contrib.auth.models import User
from django.db.models import Count
from django.test import TestCase
from django.urls import reverse

from config.tests.utils import get_login_url, silence_logging
from decks.models import Card, Deck
from decks.tests.utils import generate_card
from profiles.models import Follow
from profiles.views import ProfileListView


class ProfilesViewsTestCase(TestCase):
    """Test case focusing on the signals."""

    @classmethod
    def setUpTestData(cls):
        """Create the database data for this test.

        Specifically, it creates:
        * 4 Users
        * 6 Follow
        * 1 Hero
        * 1 Deck
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
        hero = generate_card(Card.Faction.AXIOM, Card.Type.HERO)
        Deck.objects.create(owner=user2, hero=hero, is_public=True)

    def test_list_view_unauthenticated(self):
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

    def test_list_view_authenticated(self):
        self.client.force_login(User.objects.get(username="user2"))
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

    def test_detail_view_unauthenticated(self):
        user = User.objects.get(username="user2")
        response = self.client.get(user.profile.get_absolute_url())

        user_decks = Deck.objects.filter(owner=user, is_public=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "profiles/userprofile_detail.html")
        self.assertIn("builder", response.context)
        self.assertEqual(response.context["builder"], user)
        with self.assertRaises(AttributeError):
            response.context["builder"].is_followed
        self.assertQuerySetEqual(response.context["deck_list"], user_decks)
        with self.assertRaises(AttributeError):
            response.context["deck_list"][0].is_loved
        self.assertIn("faction_distribution", response.context)
        self.assertDictEqual(
            dict(response.context["faction_distribution"]),
            {user_decks[0].hero.get_faction_display(): 1},
        )

    def test_detail_view_authenticated(self):
        user = User.objects.get(username="user2")
        self.client.force_login(User.objects.exclude(username="user2").first())

        response = self.client.get(user.profile.get_absolute_url())

        user_decks = Deck.objects.filter(owner=user, is_public=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "profiles/userprofile_detail.html")
        self.assertIn("builder", response.context)
        self.assertEqual(response.context["builder"], user)
        self.assertIsInstance(response.context["builder"].is_followed, bool)
        self.assertQuerySetEqual(response.context["deck_list"], user_decks)
        self.assertIsInstance(response.context["deck_list"][0].is_loved, bool)
        self.assertIn("faction_distribution", response.context)
        self.assertDictEqual(
            dict(response.context["faction_distribution"]),
            {user_decks[0].hero.get_faction_display(): 1},
        )

    def test_follow_user_unauthenticated(self):
        followed = User.objects.get(username="user1")

        url = reverse("profile-follow", kwargs={"code": followed.profile.code})
        response = self.client.get(url)

        self.assertRedirects(
            response, get_login_url(next=url), status_code=HTTPStatus.FOUND
        )

    def test_follow_nonexistent_user(self):
        follower = User.objects.get(username="user4")

        self.client.force_login(follower)
        with silence_logging():
            response = self.client.get(
                reverse("profile-follow", kwargs={"code": uuid4()})
            )

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, "errors/404.html")

    def test_follow_user_authenticated(self):
        follower = User.objects.get(username="user4")
        followed = User.objects.get(username="user1")
        Follow.objects.filter(follower=follower, followed=followed).delete()

        self.client.force_login(follower)
        url = reverse("profile-follow", kwargs={"code": followed.profile.code})
        response = self.client.get(url)

        self.assertRedirects(
            response, followed.profile.get_absolute_url(), status_code=HTTPStatus.FOUND
        )
        self.assertTrue(
            Follow.objects.filter(follower=follower, followed=followed).exists()
        )

        # The follow operation is idempotent
        response = self.client.get(url)

        self.assertRedirects(
            response, followed.profile.get_absolute_url(), status_code=HTTPStatus.FOUND
        )
        self.assertTrue(
            Follow.objects.filter(follower=follower, followed=followed).exists()
        )

    def test_unfollow_user_unauthenticated(self):
        followed = User.objects.get(username="user3")

        url = reverse("profile-unfollow", kwargs={"code": followed.profile.code})
        response = self.client.get(url)

        self.assertRedirects(
            response, get_login_url(next=url), status_code=HTTPStatus.FOUND
        )

    def test_unfollow_nonexistent_user(self):
        follower = User.objects.get(username="user4")

        self.client.force_login(follower)
        with silence_logging():
            response = self.client.get(
                reverse("profile-unfollow", kwargs={"code": uuid4()})
            )

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, "errors/404.html")

    def test_unfollow_user(self):
        follower = User.objects.get(username="user1")
        followed = User.objects.get(username="user3")
        self.assertTrue(
            Follow.objects.filter(follower=follower, followed=followed).exists()
        )

        self.client.force_login(follower)
        url = reverse("profile-unfollow", kwargs={"code": followed.profile.code})
        response = self.client.get(url)

        self.assertRedirects(
            response, followed.profile.get_absolute_url(), status_code=HTTPStatus.FOUND
        )
        self.assertFalse(
            Follow.objects.filter(follower=follower, followed=followed).exists()
        )

        # The unfollow operation is idempotent
        response = self.client.get(url)

        self.assertRedirects(
            response, followed.profile.get_absolute_url(), status_code=HTTPStatus.FOUND
        )
        self.assertFalse(
            Follow.objects.filter(follower=follower, followed=followed).exists()
        )
