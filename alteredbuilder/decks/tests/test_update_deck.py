from django.http import HttpResponse
from django.urls import reverse

from decks.models import CardInDeck, Deck
from .utils import BaseViewTestCase, get_login_url, silence_logging


class DeleteCardViewTestCase(BaseViewTestCase):
    """Test case focusing on the view that removes a Card from a Deck."""

    def assert_ajax_error(self, response: HttpResponse, status_code: int, error_message: str) -> None:
        """Method to verify the integrity of an error message to an AJAX request.

        Args:
            response (HttpResponse): Response received from the server.
            status_code (int): Expected HTTP status code.
            error_message (str): Expected string response for the given error.
        """
        self.assertEqual(response.status_code, status_code)
        self.assertIn("error", response.json())
        self.assertEqual(response.json()["error"]["code"], status_code)
        self.assertEqual(response.json()["error"]["message"], error_message)

    def test_delete_card_view(self):
        """Test the view to delete a Card from a Deck. It currently works via an AJAX
        call.

        Throughout this method, multiple times the logging is silenced, otherwise the
        logs for a failed/invalid request would be logged to the console and would mess
        with the unittest expected logs.
        """
        deck = Deck.objects.get(owner=self.user, name=self.PRIVATE_DECK_NAME)
        card = CardInDeck.objects.filter(deck=deck).first().card
        test_url = reverse("update-deck-id", kwargs={"pk": deck.id})
        headers = {
            "HTTP_X_REQUESTED_WITH": "XMLHttpRequest",
            "content_type": "application/json",
        }
        data = {"card_reference": card.reference, "action": "delete"}

        # Test an unauthenticated client
        response = self.client.post(test_url)
        self.assertRedirects(
            response, get_login_url("update-deck-id", pk=deck.id), status_code=302
        )

        # Test a request without the necessary headers
        self.client.force_login(self.user)
        with silence_logging():
            response = self.client.post(test_url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, b"Invalid request")

        # Test a request without using the POST method
        with silence_logging():
            response = self.client.get(test_url, **headers)
        self.assert_ajax_error(response, 400, "Invalid request")
    
        # Test a request without sending any payload
        with silence_logging():
            response = self.client.post(test_url, **headers)
        self.assert_ajax_error(response, 400, "Invalid payload")

        # Test a request targeting a non-existent deck id
        with silence_logging():
            response = self.client.post(reverse("update-deck-id", kwargs={"pk": 100_000}), **headers, data=data)
        self.assert_ajax_error(response, 404, "Deck not found")

        # Test a request providing an invalid action (should be "add" or "delete")
        wrong_data = dict(data)
        wrong_data["action"] = "test"
        with silence_logging():
            response = self.client.post(test_url, **headers, data=wrong_data)
        self.assert_ajax_error(response, 400, "Invalid payload")

        # Test a request with valid data
        response = self.client.post(test_url, **headers, data=data)
        self.assertEqual(response.status_code, 201)
        self.assertIn("data", response.json())
        self.assertEqual(response.json()["data"]["deleted"], True)

        # Test the same valid request, which should fail because the Card has already
        # been removed
        with silence_logging():
            response = self.client.post(test_url, **headers, data=data)
        self.assert_ajax_error(response, 404, "Card not found")

        # Test a request with valid data to delete a hero
        hero_data = dict(data)
        hero_data["card_reference"] = deck.hero.reference
        response = self.client.post(test_url, **headers, data=hero_data)
        self.assertEqual(response.status_code, 201)
        self.assertIn("data", response.json())
        self.assertEqual(response.json()["data"]["deleted"], True)


class DeleteCardViewTestCase(BaseViewTestCase):
    """Test case focusing on the view that deletes a Deck."""

    def test_delete_deck_unauthenticated(self):
        """Test the view attempting to delete a Deck by an unauthenticated user.
        """
        deck = Deck.objects.first()
        response = self.client.get(reverse("delete-deck-id", kwargs={"pk": deck.id}))

        self.assertRedirects(
            response, get_login_url("delete-deck-id", pk=deck.id), status_code=302
        )

    def test_delete_not_owned_deck(self):
        """Test the view attempting to delete a Deck that is owned by another user.
        """
        deck = Deck.objects.filter(owner=self.other_user).first()
        self.client.force_login(self.user)
        response = self.client.get(reverse("delete-deck-id", kwargs={"pk": deck.id}))

        # Even if the user does not own the Deck, the request fails silently. The user
        # is redirected to their list of Decks, although the Deck persists.
        self.assertRedirects(response, reverse("own-deck"), status_code=302)
        self.assertTrue(Deck.objects.filter(pk=deck.id).exists())

    def test_delete_owned_deck(self):
        """Test the view to delete a Deck by its owner.
        """
        deck = Deck.objects.filter(owner=self.user).first()
        self.client.force_login(self.user)
        response = self.client.get(reverse("delete-deck-id", kwargs={"pk": deck.id}))

        self.assertFalse(Deck.objects.filter(pk=deck.id).exists())
        # Recreate the deck that was just deleted
        deck.save()
        self.assertRedirects(response, reverse("own-deck"), status_code=302)


class DeleteCardViewTestCase(BaseViewTestCase):
    """Test case focusing on the view were a user "loves" a Deck."""

    def test_love_deck_unauthenticated(self):
        """Test the view of an unauthenticated user attempting to love a Deck.
        """
        deck = Deck.objects.first()
        response = self.client.get(reverse("love-deck-id", kwargs={"pk": deck.id}))

        self.assertRedirects(
            response, get_login_url("love-deck-id", pk=deck.id), status_code=302
        )

    def test_love_not_owned_private_deck(self):
        """Test the view of a user attempting to love a private Deck.
        """
        deck = Deck.objects.filter(owner=self.other_user, is_public=False).first()
        self.client.force_login(self.user)
        with silence_logging():
            response = self.client.get(reverse("love-deck-id", kwargs={"pk": deck.id}))

        self.assertTemplateUsed(response, "errors/403.html")

    def test_love_not_owned_public_deck(self):
        """Test the view of a user loving a Deck.
        """
        deck = Deck.objects.filter(owner=self.other_user, is_public=True).first()
        old_love_count = deck.love_count
        # Love a Deck
        self.client.force_login(self.user)
        response = self.client.get(reverse("love-deck-id", kwargs={"pk": deck.id}))

        new_deck = Deck.objects.get(pk=deck.id)
        self.assertEqual(old_love_count + 1, new_deck.love_count)
        self.assertRedirects(response, reverse("deck-detail", kwargs={"pk": deck.id}), status_code=302)

        # Un-love the same Deck
        response = self.client.get(reverse("love-deck-id", kwargs={"pk": deck.id}))

        new_deck = Deck.objects.get(pk=deck.id)
        self.assertEqual(old_love_count, new_deck.love_count)
        self.assertRedirects(response, reverse("deck-detail", kwargs={"pk": deck.id}), status_code=302)