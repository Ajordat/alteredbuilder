from http import HTTPStatus

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.test import TestCase

from config.tests.utils import get_login_url, silence_logging
from decks.models import Deck
from notifications.models import Notification, NotificationType


class NotificationViewTestCase(TestCase):

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create_user(username="user")
        another_user = User.objects.create_user(username="another user")
        deck = Deck.objects.create(owner=cls.user, name="name")
        Notification.objects.create(
            recipient=cls.user,
            verb=NotificationType.COMMENT,
            actor=another_user,
            content_type=ContentType.objects.get_for_model(deck),
            object_id=deck.id,
        )
        Notification.objects.create(
            recipient=cls.user,
            verb=NotificationType.LOVE,
            content_type=ContentType.objects.get_for_model(deck),
            object_id=deck.id,
        )

    def test_unauthenticated(self):
        notification = Notification.objects.first()

        response = self.client.get(notification.get_absolute_url())

        self.assertRedirects(
            response,
            get_login_url(next=notification.get_absolute_url()),
            status_code=HTTPStatus.FOUND,
        )

    def test_nonexistent_notification(self):

        self.client.force_login(self.user)
        with silence_logging():
            response = self.client.get(
                reverse("notification-detail", kwargs={"pk": 100_000})
            )

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_detail_invalid_notification(self):
        deck = Deck.objects.first()
        notification = Notification.objects.create(
            recipient=self.user,
            verb="value_outside_of_choices",
            content_type=ContentType.objects.get_for_model(deck),
            object_id=deck.id,
        )

        self.client.force_login(self.user)
        with silence_logging():
            response = self.client.get(notification.get_absolute_url())

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_detail_comment_notification(self):
        notification = Notification.objects.filter(
            verb=NotificationType.COMMENT
        ).first()
        notification.read = False
        notification.save()

        self.client.force_login(self.user)
        response = self.client.get(notification.get_absolute_url())

        notification.refresh_from_db()
        self.assertRedirects(response, notification.content_object.get_absolute_url())
        self.assertTrue(notification.read)

    def test_detail_love_notification(self):
        notification = Notification.objects.filter(verb=NotificationType.LOVE).first()
        notification.read = False
        notification.save()

        self.client.force_login(self.user)
        response = self.client.get(notification.get_absolute_url())

        notification.refresh_from_db()
        self.assertRedirects(response, notification.content_object.get_absolute_url())
        self.assertTrue(notification.read)
