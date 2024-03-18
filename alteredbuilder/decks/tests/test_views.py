from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from decks.models import Card, CardInDeck, Character, Deck, Hero, Landmark, Spell


class DecksViewsTestCase(TestCase):
    TEST_USER = "test_user"
    OTHER_TEST_USER = "other_test_user"
    PUBLIC_DECK_NAME = "test_public_deck"
    PRIVATE_DECK_NAME = "test_private_deck"

    @classmethod
    def setUpTestData(cls):
        hero = Hero.objects.create(
            reference="ALT_CORE_B_AX_01_C",
            name="Sierra & Oddball",
            faction=Card.Faction.AXIOM,
            type=Card.Type.HERO,
            rarity=Card.Rarity.COMMON,
        )
        character = Character.objects.create(
            reference="ALT_CORE_B_YZ_08_R2",
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
        spell = Spell.objects.create(
            reference="ALT_CORE_B_YZ_26_R2",
            name="Kraken's Wrath",
            faction=Card.Faction.AXIOM,
            type=Card.Type.SPELL,
            rarity=Card.Rarity.RARE,
            main_cost=5,
            recall_cost=5,
        )
        landmark = Landmark.objects.create(
            reference="ALT_CORE_B_LY_30_R2",
            name="The Ouroboros, Lyra Bastion",
            faction=Card.Faction.AXIOM,
            type=Card.Type.LANDMARK,
            rarity=Card.Rarity.RARE,
            main_cost=3,
            recall_cost=3,
        )
        cls.user = User.objects.create_user(username=cls.TEST_USER)
        other_user = User.objects.create_user(username=cls.OTHER_TEST_USER)
        cls.create_decks_for_user(cls.user, hero, [character, spell, landmark])
        cls.create_decks_for_user(other_user, hero, [character, spell, landmark])

    @classmethod
    def create_decks_for_user(cls, user, hero, cards):
        public_deck = Deck.objects.create(
            owner=user, name=cls.PUBLIC_DECK_NAME, hero=hero, is_public=True
        )
        private_deck = Deck.objects.create(
            owner=user, name=cls.PRIVATE_DECK_NAME, hero=hero, is_public=False
        )
        for card in cards:
            CardInDeck.objects.create(deck=public_deck, card=card, quantity=2)
            CardInDeck.objects.create(deck=private_deck, card=card, quantity=2)

    def test_homepage_redirect(self):
        response = self.client.get(reverse("index"))
        self.assertRedirects(response, reverse("deck-list"), status_code=301)

    def test_decks_home_unauthenticated(self):
        response = self.client.get(reverse("deck-list"))

        self.assertIn("deck_list", response.context)
        public_decks = Deck.objects.filter(is_public=True)
        self.assertQuerySetEqual(
            public_decks, response.context["deck_list"], ordered=False
        )

        self.assertNotIn("own_decks", response.context)

    def test_decks_home_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("deck-list"))

        self.assertIn("deck_list", response.context)
        public_decks = Deck.objects.filter(is_public=True)
        self.assertQuerySetEqual(
            public_decks, response.context["deck_list"], ordered=False
        )

        self.assertIn("own_decks", response.context)
        own_decks = Deck.objects.filter(owner=self.user)
        self.assertQuerySetEqual(
            own_decks, response.context["own_decks"], ordered=False
        )
