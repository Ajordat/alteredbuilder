from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from decks.forms import DecklistForm
from decks.models import Card, Character, Deck, Hero


class DecksFormsTestCase(TestCase):
    USER_NAME = "test_user"
    DECK_NAME = "test deck"
    HERO_REFERENCE = "ALT_CORE_B_AX_01_C"
    CHARACTER_REFERENCE = "ALT_CORE_B_YZ_08_R2"

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username=cls.USER_NAME)

        Hero.objects.create(
            reference=cls.HERO_REFERENCE,
            name="Sierra & Oddball",
            faction=Card.Faction.AXIOM,
            type=Card.Type.HERO,
            rarity=Card.Rarity.COMMON,
        )
        Character.objects.create(
            reference=cls.CHARACTER_REFERENCE,
            name="Yzmir Stargazer",
            faction=Card.Faction.AXIOM,
            type=Card.Type.CHARACTER,
            rarity=Card.Rarity.RARE,
            main_cost=1,
            recall_cost=1,
            forest_power=1,
            mountain_power=2,
            ocean_power=1,
        )

    def test_invalid_deck_only_name(self):
        form_data = {"name": self.DECK_NAME}
        form = DecklistForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_invalid_deck_only_decklist(self):
        form_data = {"decklist": f"1 {self.HERO_REFERENCE}"}
        form = DecklistForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_valid_deck(self):
        form_data = {
            "name": self.DECK_NAME,
            "decklist": f"1 {self.HERO_REFERENCE}\n3 {self.CHARACTER_REFERENCE}",
        }
        form = DecklistForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_valid_deck_unauthenticated(self):
        form_data = {
            "name": self.DECK_NAME,
            "decklist": f"1 {self.HERO_REFERENCE}\n3 {self.CHARACTER_REFERENCE}",
        }

        response = self.client.post(reverse("new-deck"), form_data)
        self.assertRedirects(
            response, f"{settings.LOGIN_URL}?next={reverse('new-deck')}"
        )

    def test_valid_deck_authenticated(self):
        form_data = {
            "name": self.DECK_NAME,
            "decklist": f"1 {self.HERO_REFERENCE}\n3 {self.CHARACTER_REFERENCE}",
        }

        self.client.force_login(self.user)
        response = self.client.post(reverse("new-deck"), form_data)

        new_deck = Deck.objects.filter(owner=self.user).get()
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
