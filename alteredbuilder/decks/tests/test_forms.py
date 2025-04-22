from http import HTTPStatus

from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.urls import reverse

from config.tests.utils import get_login_url, silence_logging
from decks.forms import CardImportForm, CommentForm, DecklistForm, DeckMetadataForm
from decks.models import Card, Comment, Deck
from decks.tests.utils import BaseFormTestCase
from decks.views.imports import NewDeckFormView


class CreateDeckFormTestCase(BaseFormTestCase):
    """Test case focusing on the form to create a new Deck."""

    def test_invalid_deck_only_name(self):
        """Validate a form creating a Deck only providing the name."""
        form_data = {"name": self.DECK_NAME}
        form = DecklistForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertFormError(form, "decklist", "This field is required.")

    def test_invalid_deck_only_decklist(self):
        """Validate a form creating a Deck only providing the decklist."""
        form_data = {"decklist": f"1 {self.HERO_REFERENCE}"}
        form = DecklistForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertFormError(form, "name", "This field is required.")

    def test_valid_deck_wrong_quantity(self):
        """Validate a form creating a Deck with an invalid amount of cards."""
        form_data = {
            "name": self.DECK_NAME,
            "decklist": f"4 {self.CHARACTER_REFERENCE}",
        }
        form = DecklistForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_valid_deck(self):
        """Validate a valid form creating a Deck."""
        form_data = {
            "name": self.DECK_NAME,
            "decklist": f"1 {self.HERO_REFERENCE}\n3 {self.CHARACTER_REFERENCE}",
        }
        form = DecklistForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_valid_deck_unauthenticated(self):
        """Attempt to submit a form creating a Deck while unauthenticated."""
        form_data = {
            "name": self.DECK_NAME,
            "decklist": f"1 {self.HERO_REFERENCE}\n3 {self.CHARACTER_REFERENCE}",
        }

        response = self.client.post(reverse("new-deck"), form_data)
        self.assertRedirects(
            response, get_login_url("new-deck"), status_code=HTTPStatus.FOUND
        )

    def test_get_params(self):
        """Request the view of a new deck with prefilled values from GET params."""
        initial_value = "testtesttest"
        self.client.force_login(self.user)

        # Test the `decklist` parameter
        response = self.client.get(reverse("new-deck") + f"?decklist={initial_value}")

        self.assertDictEqual(
            response.context["form"].initial, {"decklist": initial_value, "copy_of": None}
        )

        # Test the `hero` parameter
        response = self.client.get(reverse("new-deck") + f"?hero={initial_value}")

        self.assertDictEqual(
            response.context["form"].initial, {"decklist": f"1 {initial_value}", "copy_of": None}
        )

    def test_valid_deck_authenticated(self):
        """Attempt to submit a form creating a valid Deck."""
        form_data = {
            "name": self.DECK_NAME,
            "decklist": f"1 {self.HERO_REFERENCE}\n3 {self.CHARACTER_REFERENCE}",
        }

        self.client.force_login(self.user)
        response = self.client.post(reverse("new-deck"), form_data)

        new_deck = Deck.objects.filter(owner=self.user).latest("created_at")
        hero = Card.objects.get(reference=self.HERO_REFERENCE)
        character = Card.objects.get(reference=self.CHARACTER_REFERENCE)
        deck_cards = new_deck.cardindeck_set.all()

        self.assertRedirects(response, new_deck.get_absolute_url())
        self.assertFalse(new_deck.is_public)
        self.assertEqual(new_deck.hero, hero)
        self.assertEqual(len(deck_cards), 1)
        self.assertEqual(deck_cards[0].quantity, 3)
        self.assertEqual(deck_cards[0].card, character)

    def test_invalid_deck_wrong_reference(self):
        """Attempt to submit a form creating a Deck with an invalid reference to a
        card.
        """
        wrong_card_reference = "wrong_card_reference"
        form_data = {
            "name": self.DECK_NAME,
            "decklist": f"1 {self.HERO_REFERENCE}\n3 {wrong_card_reference}",
        }

        request = RequestFactory().post(reverse("new-deck"), form_data)
        request.user = self.user
        response = NewDeckFormView.as_view()(request)
        form: DecklistForm = response.context_data["form"]

        self.assertTrue(form.has_error("decklist"))
        self.assertIn(
            f"Card '{wrong_card_reference}' wasn't found and couldn't be imported",
            form.errors["decklist"],
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_invalid_deck_multiple_heroes(self):
        """Attempt to submit a form creating a Deck that contains multiple heroes."""
        form_data = {
            "name": self.DECK_NAME,
            "decklist": f"1 {self.HERO_REFERENCE}\n1 {self.HERO_REFERENCE}",
        }

        request = RequestFactory().post(reverse("new-deck"), form_data)
        request.user = self.user
        response = NewDeckFormView.as_view()(request)
        form: DecklistForm = response.context_data["form"]

        self.assertTrue(form.has_error("decklist"))
        self.assertIn(
            "Multiple heroes present in the decklist", form.errors["decklist"]
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_invalid_deck_wrong_format(self):
        """Attempt to submit a form creating a Deck with an incorrect format.
        This is useful as the DecklistForm only checks that at least one line respects
        the format.
        """
        wrong_format_line = "NOT_THE_RIGHT_FORMAT"
        form_data = {
            "name": self.DECK_NAME,
            "decklist": f"1 {self.HERO_REFERENCE}\n{wrong_format_line}",
        }

        request = RequestFactory().post(reverse("new-deck"), form_data)
        request.user = self.user
        response = NewDeckFormView.as_view()(request)
        form: DecklistForm = response.context_data["form"]

        self.assertTrue(form.has_error("decklist"))
        self.assertIn(
            f"Failed to unpack '{wrong_format_line}'", form.errors["decklist"]
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_valid_deck_missing_hero(self):
        """Submit a form creating a Deck without a hero reference, which is a valid Deck model."""
        form_data = {
            "name": self.DECK_NAME,
            "decklist": f"3 {self.CHARACTER_REFERENCE}",
        }

        self.client.force_login(self.user)
        response = self.client.post(reverse("new-deck"), form_data)

        new_deck = Deck.objects.filter(owner=self.user).latest("created_at")
        character = Card.objects.get(reference=self.CHARACTER_REFERENCE)
        deck_cards = new_deck.cardindeck_set.all()

        self.assertRedirects(response, new_deck.get_absolute_url())
        self.assertFalse(new_deck.is_public)
        self.assertEqual(new_deck.hero, None)
        self.assertEqual(len(deck_cards), 1)
        self.assertEqual(deck_cards[0].quantity, 3)
        self.assertEqual(deck_cards[0].card, character)

    def test_valid_deck_repeated_card(self):
        """Submit a form creating a Deck with multiple references to the same card.
        The CardInDeck should be aggregated.
        """
        form_data = {
            "name": self.DECK_NAME,
            "decklist": f"3 {self.CHARACTER_REFERENCE}\n2 {self.CHARACTER_REFERENCE}",
        }

        self.client.force_login(self.user)
        response = self.client.post(reverse("new-deck"), form_data)

        new_deck = Deck.objects.filter(owner=self.user).latest("created_at")
        character = Card.objects.get(reference=self.CHARACTER_REFERENCE)
        deck_cards = new_deck.cardindeck_set.all()

        self.assertRedirects(response, new_deck.get_absolute_url())
        self.assertFalse(new_deck.is_public)
        self.assertEqual(new_deck.hero, None)
        self.assertEqual(len(deck_cards), 1)
        self.assertEqual(deck_cards[0].quantity, 5)
        self.assertEqual(deck_cards[0].card, character)


class UpdateDeckMetadataFormTestCase(BaseFormTestCase):
    """Test case focusing on the form to update the metadata of a Deck."""

    def test_invalid_no_name(self):
        """Validate a form providing no name field."""
        form_data = {}
        form = DeckMetadataForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertFormError(form, "name", "This field is required.")

        form_data = {"name": ""}
        form = DeckMetadataForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertFormError(form, "name", "This field is required.")

    def test_valid_deck_unauthenticated(self):
        """Attempt to submit a form updating a Deck's metadata while unauthenticated."""
        deck = Deck.objects.first()
        form_data = {"name": "new name", "description": "new description"}

        response = self.client.post(
            reverse("update-deck-metadata", kwargs={"pk": deck.id}), form_data
        )
        self.assertRedirects(
            response,
            get_login_url("update-deck-metadata", pk=deck.id),
            status_code=HTTPStatus.FOUND,
        )

    def test_valid_not_owned_deck(self):
        """Attempt to submit a form updating the metadata of another user's Deck."""
        deck = Deck.objects.exclude(owner=self.user).first()
        form_data = {"name": "new name", "description": "new description"}

        self.client.force_login(self.user)
        with silence_logging():
            response = self.client.post(
                reverse("update-deck-metadata", kwargs={"pk": deck.id}), form_data
            )

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_valid_nonexistent_deck(self):
        """Attempt to submit a form updating the metadata of a nonexistent Deck."""
        form_data = {"name": "new name", "description": "new description"}

        self.client.force_login(self.user)
        with silence_logging():
            response = self.client.post(
                reverse("update-deck-metadata", kwargs={"pk": 100_000}), form_data
            )

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_valid_submission(self):
        """Submit a form updating a the metadata of a Deck."""
        deck = Deck.objects.filter(owner=self.user).first()
        form_data = {
            "name": f"Old name: [{deck.name}]",
            "description": f"Old description: [{deck.description}]",
        }

        self.client.force_login(self.user)
        response = self.client.post(
            reverse("update-deck-metadata", kwargs={"pk": deck.id}), form_data
        )

        deck.refresh_from_db()
        self.assertEqual(deck.name, form_data["name"])
        self.assertEqual(deck.description, form_data["description"])
        self.assertRedirects(
            response, deck.get_absolute_url(), status_code=HTTPStatus.FOUND
        )


class CreateCommentFormTestCase(BaseFormTestCase):
    """Test case focusing on the form to create a Comment."""

    def test_invalid_no_body(self):
        """Validate a form providing no body field."""
        form_data = {}
        form = CommentForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertFormError(form, "body", "This field is required.")

        form_data = {"body": ""}
        form = CommentForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertFormError(form, "body", "This field is required.")

    def test_valid_comment_unauthenticated(self):
        """Attempt to submit a form creating a Comment while unauthenticated."""
        deck = Deck.objects.first()
        form_data = {"body": "comment text"}

        response = self.client.post(
            reverse("create-deck-comment", kwargs={"pk": deck.id}), form_data
        )

        self.assertRedirects(
            response,
            get_login_url("create-deck-comment", pk=deck.id),
            status_code=HTTPStatus.FOUND,
        )

    def test_valid_nonexistent_deck(self):
        """Attempt to submit a form creating a Comment on a nonexistent Deck."""
        form_data = {"body": "comment text"}

        self.client.force_login(self.user)
        with silence_logging():
            response = self.client.post(
                reverse("create-deck-comment", kwargs={"pk": 100_000}), form_data
            )

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_valid_submission(self):
        """Submit a form creating a Comment."""
        deck = Deck.objects.filter(owner=self.other_user, is_public=True).first()
        form_data = {"body": "comment text"}

        self.client.force_login(self.user)
        response = self.client.post(
            reverse("create-deck-comment", kwargs={"pk": deck.id}), form_data
        )

        comment_count = deck.comment_count
        deck.refresh_from_db()
        self.assertEqual(comment_count + 1, deck.comment_count)
        self.assertTrue(
            Comment.objects.filter(
                user=self.user, deck=deck, body=form_data["body"]
            ).exists()
        )
        self.assertRedirects(
            response, deck.get_absolute_url(), status_code=HTTPStatus.FOUND
        )


class ImportCardFormTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="user")

    def test_form_invalid_reference(self):
        form = CardImportForm(data={"reference": "asdf"})

        self.assertFalse(form.is_valid())
        self.assertFormError(
            form,
            "reference",
            "Invalid value. The reference should look similar to 'ALT_COREKS_B_OR_21_U_2139'.",
        )

    def test_form_valid_references(self):
        references = [
            "ALT_CORE_B_LY_04_U_1",
            "ALT_COREKS_B_LY_04_U_125",
            "ALT_CORE_P_MU_52_U_14",
        ]

        for reference in references:
            form = CardImportForm(data={"reference": reference})

            self.assertTrue(form.is_valid())

    def test_get_unauthenticated(self):
        response = self.client.get(reverse("import-card"))

        self.assertRedirects(
            response, get_login_url("import-card"), status_code=HTTPStatus.FOUND
        )

    def test_get_authenticated(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("import-card"))

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "decks/import_card.html")
        self.assertIn("form", response.context)
        self.assertIsInstance(response.context["form"], CardImportForm)
        self.assertIsNone(response.context["form"].initial["reference"])

    def test_get_authenticated_with_params(self):
        test_reference = "real_reference"
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("import-card") + "?reference=" + test_reference
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "decks/import_card.html")
        self.assertIn("form", response.context)
        self.assertIsInstance(response.context["form"], CardImportForm)
        self.assertEqual(response.context["form"].initial["reference"], test_reference)

    # def test_invalid_card_wrong_reference(self):
    #     form_data = {"reference": "asdf"}
    #     request = RequestFactory().post(reverse("import-card"), form_data)
    #     request.user = self.user

    #     response = import_card(request)

    #     self.assertTrue(form.has_error("decklist"))
    #     self.assertFormError(form, "reference", "Enter a valid value.")
    #     self.assertEqual(response.status_code, HTTPStatus.OK)
