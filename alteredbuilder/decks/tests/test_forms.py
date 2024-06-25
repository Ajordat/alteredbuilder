from django.test import RequestFactory
from django.urls import reverse

from decks.forms import DecklistForm, DeckMetadataForm
from decks.models import Card, CardInDeck, Character, Deck, Hero
from decks.views import NewDeckFormView
from .utils import BaseFormTestCase, generate_card, get_login_url, silence_logging


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
        self.assertRedirects(response, get_login_url("new-deck"), status_code=302)

    def test_valid_deck_authenticated(self):
        """Attempt to submit a form creating a valid Deck."""
        form_data = {
            "name": self.DECK_NAME,
            "decklist": f"1 {self.HERO_REFERENCE}\n3 {self.CHARACTER_REFERENCE}",
        }

        self.client.force_login(self.user)
        response = self.client.post(reverse("new-deck"), form_data)

        new_deck = Deck.objects.filter(owner=self.user).latest("created_at")
        hero = Hero.objects.get(reference=self.HERO_REFERENCE)
        character = Character.objects.get(reference=self.CHARACTER_REFERENCE)
        deck_cards = new_deck.cardindeck_set.all()

        self.assertRedirects(
            response, reverse("deck-detail", kwargs={"pk": new_deck.id})
        )
        self.assertFalse(new_deck.is_public)
        self.assertEqual(new_deck.hero, hero)
        self.assertEqual(len(deck_cards), 1)
        self.assertEqual(deck_cards[0].quantity, 3)
        self.assertEqual(deck_cards[0].card.character, character)

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
            f"Card '{wrong_card_reference}' does not exist", form.errors["decklist"]
        )
        self.assertEqual(response.status_code, 200)

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
            f"Multiple heroes present in the decklist", form.errors["decklist"]
        )
        self.assertEqual(response.status_code, 200)

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
        self.assertEqual(response.status_code, 200)

    def test_valid_deck_missing_hero(self):
        """Submit a form creating a Deck without a hero reference, which is a valid Deck model."""
        form_data = {
            "name": self.DECK_NAME,
            "decklist": f"3 {self.CHARACTER_REFERENCE}",
        }

        self.client.force_login(self.user)
        response = self.client.post(reverse("new-deck"), form_data)

        new_deck = Deck.objects.filter(owner=self.user).latest("created_at")
        character = Character.objects.get(reference=self.CHARACTER_REFERENCE)
        deck_cards = new_deck.cardindeck_set.all()

        self.assertRedirects(
            response, reverse("deck-detail", kwargs={"pk": new_deck.id})
        )
        self.assertFalse(new_deck.is_public)
        self.assertEqual(new_deck.hero, None)
        self.assertEqual(len(deck_cards), 1)
        self.assertEqual(deck_cards[0].quantity, 3)
        self.assertEqual(deck_cards[0].card.character, character)


class AddCardFormTestCase(BaseFormTestCase):
    """Test case focusing on the form to add a Card to a Deck."""

    def test_update_deck_add_existing_card(self):
        character = Character.objects.first()
        deck = Deck.objects.filter(owner=self.user).first()
        cid = CardInDeck.objects.create(deck=deck, card=character, quantity=1)

        form_data = {
            "deck_id": deck.id,
            "card_reference": character.reference,
            "quantity": 2,
        }

        self.client.force_login(self.user)
        response = self.client.post(reverse("update-deck"), form_data)
        cid.refresh_from_db()

        self.assertEqual(cid.quantity, 3)
        self.assertRedirects(response, reverse("cards"))

    def test_update_deck_add_new_card(self):
        character = generate_card(
            Card.Faction.AXIOM, Card.Type.CHARACTER, Card.Rarity.RARE
        )
        deck = Deck.objects.filter(owner=self.user).first()
        form_data = {
            "deck_id": deck.id,
            "card_reference": character.reference,
            "quantity": 2,
        }

        self.client.force_login(self.user)
        response = self.client.post(reverse("update-deck"), form_data)
        cid = CardInDeck.objects.filter(deck=deck, card=character).get()

        self.assertEqual(cid.quantity, 2)
        self.assertRedirects(response, reverse("cards"))

    def test_update_deck_add_hero(self):
        hero = Hero.objects.get(reference=self.HERO_REFERENCE)
        deck = Deck.objects.create(owner=self.user, name=self.DECK_NAME)
        form_data = {
            "deck_id": deck.id,
            "card_reference": hero.reference,
            "quantity": 2,
        }

        self.client.force_login(self.user)
        response = self.client.post(reverse("update-deck"), form_data)

        deck.refresh_from_db()
        self.assertEqual(deck.hero.reference, hero.reference)
        self.assertRedirects(response, reverse("cards"))

        other_hero = Hero.objects.exclude(reference=self.HERO_REFERENCE).first()
        form_data["card_reference"] = other_hero.reference
        response = self.client.post(reverse("update-deck"), form_data)

        deck.refresh_from_db()
        self.assertEqual(deck.hero.reference, hero.reference)
        self.assertNotEqual(deck.hero.reference, other_hero.reference)
        self.assertRedirects(response, reverse("cards"))


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
            status_code=302,
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

        # For an unknown reason, this is returning 405 instead of 403
        self.assertEqual(response.status_code, 405)

    def test_valid_non_existent_deck(self):
        """Attempt to submit a form updating the metadata of a non-existent Deck."""
        form_data = {"name": "new name", "description": "new description"}

        self.client.force_login(self.user)
        with silence_logging():
            response = self.client.post(
                reverse("update-deck-metadata", kwargs={"pk": 100_000}), form_data
            )

        # For an unknown reason, this is returning 405 instead of 403
        self.assertEqual(response.status_code, 405)

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
            response, reverse("deck-detail", kwargs={"pk": deck.id}), status_code=302
        )
