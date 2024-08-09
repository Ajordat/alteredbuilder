from http import HTTPStatus

from django.urls import reverse

from config.tests.utils import get_login_url, silence_logging
from decks.models import Card, CardInDeck, Comment, CommentVote, Deck
from decks.tests.utils import AjaxTestCase, BaseViewTestCase


class UpdateDeckViewTestCase(BaseViewTestCase, AjaxTestCase):
    """Test case focusing on the view that modifies the content of a Deck."""

    def test_ajax_request(self):
        deck = Deck.objects.get(owner=self.user, name=self.PRIVATE_DECK_NAME)
        test_url = reverse("update-deck-id", kwargs={"pk": deck.id})

        self.assert_ajax_protocol(test_url, self.user)

    def test_unauthenticated(self):
        """Test the view to add a Card to a Deck with an unauthenticated user."""
        deck = Deck.objects.get(owner=self.user, name=self.PRIVATE_DECK_NAME)
        test_url = reverse("update-deck-id", kwargs={"pk": deck.id})
        headers = {
            "HTTP_X_REQUESTED_WITH": "XMLHttpRequest",
            "content_type": "application/json",
        }

        response = self.client.post(test_url, **headers)

        self.assertRedirects(
            response, get_login_url(next=test_url), status_code=HTTPStatus.FOUND
        )

    def test_add_card_view(self):
        """Test the view to add a Card to a Deck. It currently works via an AJAX call.

        In practice, this action is not implemented with this call and bears no results
        other than validating the received data.
        """
        deck = Deck.objects.get(owner=self.user, name=self.PRIVATE_DECK_NAME)
        test_url = reverse("update-deck-id", kwargs={"pk": deck.id})
        headers = {
            "HTTP_X_REQUESTED_WITH": "XMLHttpRequest",
            "content_type": "application/json",
        }
        data = {"action": "add"}
        self.client.force_login(self.user)

        response = self.client.post(test_url, **headers, data=data)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn("data", response.json())
        self.assertFalse(response.json()["data"]["added"])

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
        self.client.force_login(self.user)

        # Test a request targeting a nonexistent deck id
        with silence_logging():
            response = self.client.post(
                reverse("update-deck-id", kwargs={"pk": 100_000}), **headers, data=data
            )

        self.assert_ajax_error(response, HTTPStatus.NOT_FOUND, "Deck not found")

        # Test a request without sending any payload
        with silence_logging():
            response = self.client.post(test_url, **headers)

        self.assert_ajax_error(response, HTTPStatus.BAD_REQUEST, "Invalid payload")

        # Test a request providing an invalid action (should be "add", "delete" or
        # "patch")
        wrong_data = dict(data)
        wrong_data["action"] = "test"

        with silence_logging():
            response = self.client.post(test_url, **headers, data=wrong_data)

        self.assert_ajax_error(response, HTTPStatus.BAD_REQUEST, "Invalid payload")

        # Test a request with valid data
        response = self.client.post(test_url, **headers, data=data)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn("data", response.json())
        self.assertTrue(response.json()["data"]["deleted"])

        # Test the same valid request, which should fail because the Card has already
        # been removed
        with silence_logging():
            response = self.client.post(test_url, **headers, data=data)

        self.assert_ajax_error(response, HTTPStatus.NOT_FOUND, "Card not found")

        # Test a request with valid data to delete a hero
        hero_data = dict(data)
        hero_data["card_reference"] = deck.hero.reference

        response = self.client.post(test_url, **headers, data=hero_data)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn("data", response.json())
        self.assertTrue(response.json()["data"]["deleted"])

    def test_patch_deck_view(self):
        """Test the view to patch a Deck. It currently works via an AJAX call.

        Throughout this method, multiple times the logging is silenced, otherwise the
        logs for a failed/invalid request would be logged to the console and would mess
        with the unittest expected logs.
        """
        deck = Deck.objects.get(owner=self.user, name=self.PRIVATE_DECK_NAME)
        cid = CardInDeck.objects.filter(deck=deck).first()
        test_url = reverse("update-deck-id", kwargs={"pk": deck.id})
        headers = {
            "HTTP_X_REQUESTED_WITH": "XMLHttpRequest",
            "content_type": "application/json",
        }
        data = {
            "name": "deck name",
            "decklist": {cid.card.reference: cid.quantity},
            "action": "patch",
        }
        self.client.force_login(self.user)

        # Test a request without giving a name
        with silence_logging():
            response = self.client.post(test_url, **headers, data={"action": "patch"})

        self.assert_ajax_error(response, HTTPStatus.BAD_REQUEST, "Invalid payload")

        # Test a request with an empty name
        with silence_logging():
            response = self.client.post(
                test_url, **headers, data={"action": "patch", "name": ""}
            )

        self.assert_ajax_error(
            response, HTTPStatus.UNPROCESSABLE_ENTITY, "The deck must have a name"
        )

        # Test a request targeting a nonexistent deck id
        with silence_logging():
            response = self.client.post(
                reverse("update-deck-id", kwargs={"pk": 100_000}), **headers, data=data
            )
        self.assert_ajax_error(response, HTTPStatus.NOT_FOUND, "Deck not found")

        # Test a request providing an invalid action (should be "add" or "delete")
        wrong_data = dict(data)
        wrong_data["action"] = "test"

        with silence_logging():
            response = self.client.post(test_url, **headers, data=wrong_data)

        self.assert_ajax_error(response, HTTPStatus.BAD_REQUEST, "Invalid payload")

        # Test a request to add a card
        target_quantity = cid.quantity + 2
        extra_data = dict(data)
        extra_data["decklist"] = {
            cid.card.reference: target_quantity,
            "wrong_reference": 2,
        }

        response = self.client.post(test_url, **headers, data=extra_data)

        cid.refresh_from_db()
        deck.refresh_from_db()
        response_data = response.json()["data"]
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn("data", response.json())
        self.assertTrue(response_data["patched"])
        self.assertEqual(response_data["deck"], deck.id)
        self.assertEqual(cid.quantity, target_quantity)
        self.assertEqual(deck.name, extra_data["name"])

        # Test a request creating a new deck
        response = self.client.post(
            reverse("update-deck-id", kwargs={"pk": 0}), **headers, data=data
        )

        response_data = response.json()["data"]
        new_deck = Deck.objects.get(id=response_data["deck"])
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(response_data["patched"])
        self.assertEqual(new_deck.name, data["name"])
        self.assertEqual(new_deck.cardindeck_set.count(), len(data["decklist"]))
        for new_cid in new_deck.cardindeck_set.all():
            self.assertIn(new_cid.card.reference, data["decklist"])
            self.assertEqual(new_cid.quantity, data["decklist"][new_cid.card.reference])

        # Test a request to remove a card
        target_quantity = 0
        data["decklist"] = {cid.card.reference: target_quantity}

        response = self.client.post(test_url, **headers, data=data)

        deck.refresh_from_db()
        response_data = response.json()["data"]
        self.assertRaises(CardInDeck.DoesNotExist, cid.refresh_from_db)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(response_data["patched"])
        self.assertEqual(response_data["deck"], deck.id)
        self.assertEqual(deck.name, data["name"])

        # Test a request with valid data to delete a hero
        hero_data = dict(data)
        hero_data["decklist"] = {deck.hero.reference: 0}

        response = self.client.post(test_url, **headers, data=hero_data)

        deck.refresh_from_db()
        response_data = response.json()["data"]
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn("data", response.json())
        self.assertTrue(response_data["patched"])
        self.assertEqual(response_data["deck"], deck.id)
        self.assertIsNone(deck.hero)

        # Test a request with valid data to add a hero
        hero = Card.objects.filter(type=Card.Type.HERO).first()
        hero_data["decklist"] = {hero.reference: 1}

        response = self.client.post(test_url, **headers, data=hero_data)

        deck.refresh_from_db()
        response_data = response.json()["data"]
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(response_data["patched"])
        self.assertEqual(response_data["deck"], deck.id)
        self.assertEqual(deck.hero, hero)


class DeleteDeckViewTestCase(BaseViewTestCase):
    """Test case focusing on the view that deletes a Deck."""

    def test_delete_deck_unauthenticated(self):
        """Test the view attempting to delete a Deck by an unauthenticated user."""
        deck = Deck.objects.first()
        response = self.client.get(reverse("delete-deck-id", kwargs={"pk": deck.id}))

        self.assertRedirects(
            response,
            get_login_url("delete-deck-id", pk=deck.id),
            status_code=HTTPStatus.FOUND,
        )

    def test_delete_not_owned_deck(self):
        """Test the view attempting to delete a Deck that is owned by another user."""
        deck = Deck.objects.filter(owner=self.other_user).first()
        self.client.force_login(self.user)
        response = self.client.get(reverse("delete-deck-id", kwargs={"pk": deck.id}))

        # Even if the user does not own the Deck, the request fails silently. The user
        # is redirected to their list of Decks, although the Deck persists.
        self.assertRedirects(
            response, reverse("own-deck"), status_code=HTTPStatus.FOUND
        )
        self.assertTrue(Deck.objects.filter(pk=deck.id).exists())

    def test_delete_owned_deck(self):
        """Test the view to delete a Deck by its owner."""
        deck = Deck.objects.filter(owner=self.user).first()
        self.client.force_login(self.user)
        response = self.client.get(reverse("delete-deck-id", kwargs={"pk": deck.id}))

        self.assertFalse(Deck.objects.filter(pk=deck.id).exists())
        # Recreate the deck that was just deleted
        deck.save()
        self.assertRedirects(
            response, reverse("own-deck"), status_code=HTTPStatus.FOUND
        )


class LoveDeckViewTestCase(BaseViewTestCase):
    """Test case focusing on the view were a user "loves" a Deck."""

    def test_love_deck_unauthenticated(self):
        """Test the view of an unauthenticated user attempting to love a Deck."""
        deck = Deck.objects.first()
        response = self.client.get(reverse("love-deck-id", kwargs={"pk": deck.id}))

        self.assertRedirects(
            response,
            get_login_url("love-deck-id", pk=deck.id),
            status_code=HTTPStatus.FOUND,
        )

    def test_love_not_owned_private_deck(self):
        """Test the view of a user attempting to love a private Deck."""
        deck = Deck.objects.filter(owner=self.other_user, is_public=False).first()
        self.client.force_login(self.user)
        with silence_logging():
            response = self.client.get(reverse("love-deck-id", kwargs={"pk": deck.id}))

        self.assertTemplateUsed(response, "errors/403.html")

    def test_love_not_owned_public_deck(self):
        """Test the view of a user loving a Deck."""
        deck = Deck.objects.filter(owner=self.other_user, is_public=True).first()
        old_love_count = deck.love_count
        # Love a Deck
        self.client.force_login(self.user)
        response = self.client.get(reverse("love-deck-id", kwargs={"pk": deck.id}))

        new_deck = Deck.objects.get(pk=deck.id)
        self.assertEqual(old_love_count + 1, new_deck.love_count)
        self.assertRedirects(
            response, deck.get_absolute_url(), status_code=HTTPStatus.FOUND
        )

        # Un-love the same Deck
        response = self.client.get(reverse("love-deck-id", kwargs={"pk": deck.id}))

        new_deck = Deck.objects.get(pk=deck.id)
        self.assertEqual(old_love_count, new_deck.love_count)
        self.assertRedirects(
            response, deck.get_absolute_url(), status_code=HTTPStatus.FOUND
        )


class VoteCommentViewTestCase(BaseViewTestCase, AjaxTestCase):
    """Test case focusing on the view that votes for a Comment in a Deck."""

    def test_ajax_request(self):
        deck = Deck.objects.get(owner=self.user, name=self.PUBLIC_DECK_NAME)
        comment = Comment.objects.get(user=self.user, deck=deck)
        test_url = reverse(
            "vote-comment", kwargs={"pk": deck.id, "comment_pk": comment.id}
        )

        self.assert_ajax_protocol(test_url, self.user)

    def test_vote_comment_unauthenticated(self):
        """Test the view to vote a Comment with an unauthenticated user."""
        deck = Deck.objects.get(owner=self.user, name=self.PUBLIC_DECK_NAME)
        comment = Comment.objects.get(user=self.user, deck=deck)
        test_url = reverse(
            "vote-comment", kwargs={"pk": deck.id, "comment_pk": comment.id}
        )
        headers = {
            "HTTP_X_REQUESTED_WITH": "XMLHttpRequest",
            "content_type": "application/json",
        }

        response = self.client.post(test_url, **headers)

        self.assertRedirects(
            response, get_login_url(next=test_url), status_code=HTTPStatus.FOUND
        )

    def test_vote_comment_authenticated(self):
        """Test the view to vote a Comment with an authenticated user."""
        deck = Deck.objects.get(owner=self.user, name=self.PUBLIC_DECK_NAME)
        comment = Comment.objects.get(user=self.user, deck=deck)
        test_url = reverse(
            "vote-comment", kwargs={"pk": deck.id, "comment_pk": comment.id}
        )
        headers = {
            "HTTP_X_REQUESTED_WITH": "XMLHttpRequest",
            "content_type": "application/json",
        }

        # Vote a Comment, which will increase its vote_count and create a CommentVote
        self.client.force_login(self.other_user)
        response = self.client.post(test_url, **headers)

        response_data = response.json()["data"]
        comment_vote_count = comment.vote_count
        comment.refresh_from_db()
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(comment_vote_count + 1, comment.vote_count)
        self.assertTrue(response_data["created"])
        self.assertTrue(
            CommentVote.objects.filter(user=self.other_user, comment=comment).exists()
        )

        # Vote the same Comment again, which will decrease its vote_count and delete
        # the CommentVote
        response = self.client.post(test_url, **headers)

        response_data = response.json()["data"]
        comment_vote_count = comment.vote_count
        comment.refresh_from_db()
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(comment_vote_count - 1, comment.vote_count)
        self.assertTrue(response_data["deleted"])
        self.assertFalse(
            CommentVote.objects.filter(user=self.other_user, comment=comment).exists()
        )

    def test_vote_comment_nonexistent_deck(self):
        """Attempt to vote a Comment from a nonexistent Deck."""
        comment = Comment.objects.first()
        test_url = reverse(
            "vote-comment", kwargs={"pk": 100_000, "comment_pk": comment.id}
        )
        headers = {
            "HTTP_X_REQUESTED_WITH": "XMLHttpRequest",
            "content_type": "application/json",
        }

        self.client.force_login(self.user)
        with silence_logging():
            response = self.client.post(test_url, **headers)

        self.assert_ajax_error(response, HTTPStatus.NOT_FOUND, "Comment not found")

    def test_vote_nonexistent_comment(self):
        """Attempt to vote a nonexistent Comment."""
        deck = Deck.objects.get(owner=self.user, name=self.PUBLIC_DECK_NAME)
        test_url = reverse(
            "vote-comment", kwargs={"pk": deck.id, "comment_pk": 100_000}
        )
        headers = {
            "HTTP_X_REQUESTED_WITH": "XMLHttpRequest",
            "content_type": "application/json",
        }

        self.client.force_login(self.user)
        with silence_logging():
            response = self.client.post(test_url, **headers)

        self.assert_ajax_error(response, HTTPStatus.NOT_FOUND, "Comment not found")


class DeleteCommentViewTestCase(BaseViewTestCase, AjaxTestCase):
    """Test case focusing on the view that deletes a Comment from a Deck."""

    def test_ajax_request(self):
        deck = Deck.objects.get(owner=self.user, name=self.PUBLIC_DECK_NAME)
        comment = Comment.objects.get(user=self.user, deck=deck)
        test_url = reverse(
            "delete-comment", kwargs={"pk": deck.id, "comment_pk": comment.id}
        )

        self.assert_ajax_protocol(test_url, self.user)

    def test_delete_comment_unauthenticated(self):
        """Test the view to delete a Comment with an unauthenticated user."""
        deck = Deck.objects.get(owner=self.user, name=self.PUBLIC_DECK_NAME)
        comment = Comment.objects.get(user=self.user, deck=deck)
        test_url = reverse(
            "delete-comment", kwargs={"pk": deck.id, "comment_pk": comment.id}
        )
        headers = {
            "HTTP_X_REQUESTED_WITH": "XMLHttpRequest",
            "content_type": "application/json",
        }

        response = self.client.post(test_url, **headers)

        self.assertRedirects(
            response, get_login_url(next=test_url), status_code=HTTPStatus.FOUND
        )

    def test_delete_comment_nonexistent_deck(self):
        """Attempt to delete a Comment from a nonexistent Deck."""
        comment = Comment.objects.first()
        test_url = reverse(
            "delete-comment", kwargs={"pk": 100_000, "comment_pk": comment.id}
        )
        headers = {
            "HTTP_X_REQUESTED_WITH": "XMLHttpRequest",
            "content_type": "application/json",
        }

        self.client.force_login(self.user)
        with silence_logging():
            response = self.client.post(test_url, **headers)

        self.assert_ajax_error(response, HTTPStatus.NOT_FOUND, "Deck not found")

    def test_delete_nonexistent_comment(self):
        """Attempt to delete a nonexistent Comment."""
        deck = Deck.objects.get(owner=self.user, name=self.PUBLIC_DECK_NAME)
        test_url = reverse(
            "delete-comment", kwargs={"pk": deck.id, "comment_pk": 100_000}
        )
        headers = {
            "HTTP_X_REQUESTED_WITH": "XMLHttpRequest",
            "content_type": "application/json",
        }

        self.client.force_login(self.user)
        with silence_logging():
            response = self.client.post(test_url, **headers)

        self.assert_ajax_error(response, HTTPStatus.NOT_FOUND, "Comment not found")

    def test_delete_not_owned_comment(self):
        """Test the view to delete a Comment with an authenticated user that didn't create it."""
        deck = Deck.objects.get(owner=self.user, name=self.PUBLIC_DECK_NAME)
        comment = Comment.objects.get(user=self.user, deck=deck)
        test_url = reverse(
            "delete-comment", kwargs={"pk": deck.id, "comment_pk": comment.id}
        )
        headers = {
            "HTTP_X_REQUESTED_WITH": "XMLHttpRequest",
            "content_type": "application/json",
        }

        self.client.force_login(self.other_user)
        with silence_logging():
            response = self.client.post(test_url, **headers)

        self.assert_ajax_error(response, HTTPStatus.NOT_FOUND, "Comment not found")

    def test_delete_owned_comment(self):
        """Test the view to delete a Comment with the authenticated user that created it."""
        deck = Deck.objects.get(owner=self.user, name=self.PUBLIC_DECK_NAME)
        comment = Comment.objects.get(user=self.user, deck=deck)
        test_url = reverse(
            "delete-comment", kwargs={"pk": deck.id, "comment_pk": comment.id}
        )
        headers = {
            "HTTP_X_REQUESTED_WITH": "XMLHttpRequest",
            "content_type": "application/json",
        }

        self.client.force_login(self.user)
        response = self.client.post(test_url, **headers)

        response_data = response.json()["data"]
        comment_count = deck.comment_count
        deck.refresh_from_db()
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(comment_count - 1, deck.comment_count)
        self.assertTrue(response_data["deleted"])
        with self.assertRaises(Comment.DoesNotExist):
            comment.refresh_from_db()
