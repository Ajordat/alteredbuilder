from http import HTTPStatus
from unittest import skipIf

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch

from config.tests.utils import silence_logging
from decks.models import Deck


class RouterTestCase(TestCase):

    def test_initial_redirect(self):
        """Test case verifying that the index page redirects to the landing page."""
        response = self.client.get("/")

        self.assertRedirects(response, reverse("home"), HTTPStatus.MOVED_PERMANENTLY)

    def test_robots(self):
        response = self.client.get(reverse("robots.txt"))

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.headers["Content-Type"], "text/plain")
        self.assertTemplateUsed(response, "robots.txt")

    def test_sitemap(self):
        # The creation of a Deck with a description enforces the usage of
        # `config.sitemaps.DeckSitemap`
        user = User.objects.create_user(username="test_user")
        Deck.objects.create(
            owner=user,
            name="public deck",
            is_public=True,
            description="cool description",
        )
        response = self.client.get(reverse("django.contrib.sitemaps.views.sitemap"))

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.headers["Content-Type"], "application/xml")

    @skipIf(settings.DEBUG is True, "Only ensure when DEBUG=False")
    def test_django_debug_toolbar(self):
        with self.assertRaises(NoReverseMatch):
            reverse("render_panel")

    def test_404(self):
        with silence_logging():
            response = self.client.get("/this/page/doesnt/exist/")

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed("errors/404.html")
        self.assertNotIn("reason", response.context)

        superuser = User.objects.create_superuser(username="admin")
        self.client.force_login(superuser)
        with silence_logging():
            response = self.client.get("/this/page/doesnt/exist/")

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateNotUsed("errors/404.html")
        self.assertIn("reason", response.context)
