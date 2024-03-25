from django.contrib.auth.models import User
from django.http import HttpResponse
from django.test import TestCase
from django.urls import reverse

from decks.models import Card, CardInDeck, Character, Deck, Hero, Permanent, Spell


class DecksViewsTestCase(TestCase):
    """Test case focusing on the Views."""

    TEST_USER = "test_user"
    OTHER_TEST_USER = "other_test_user"
    PUBLIC_DECK_NAME = "test_public_deck"
    PRIVATE_DECK_NAME = "test_private_deck"

    @classmethod
    def setUpTestData(cls):
        """Create the database data for this test.

        Specifically, it creates:
        * 2 User
        * 1 Hero
        * 1 Character
        * 1 Spell
        * 1 Permanent
        * 4 Deck
        """
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
        permanent = Permanent.objects.create(
            reference="ALT_CORE_B_LY_30_R2",
            name="The Ouroboros, Lyra Bastion",
            faction=Card.Faction.AXIOM,
            type=Card.Type.PERMANENT,
            rarity=Card.Rarity.RARE,
            main_cost=3,
            recall_cost=3,
        )
        cls.user = User.objects.create_user(username=cls.TEST_USER)
        cls.other_user = User.objects.create_user(username=cls.OTHER_TEST_USER)
        cls.create_decks_for_user(cls.user, hero, [character, spell, permanent])
        cls.create_decks_for_user(cls.other_user, hero, [character, spell, permanent])

    @classmethod
    def create_decks_for_user(cls, user: User, hero: Hero, cards: list[Card]):
        """Create a public and a private deck based on the received parameters.

        Args:
            user (User): The owner of the decks.
            hero (Hero): The Deck's Hero.
            cards (list[Card]): The Deck's cards.
        """
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
        """Test that the index page redirects to the entry endpoint."""
        response = self.client.get(reverse("index"))
        self.assertRedirects(response, reverse("deck-list"), status_code=301)

    def test_decks_home_unauthenticated(self):
        """Test the context content for an unauthenticated user."""
        response = self.client.get(reverse("deck-list"))

        self.assertIn("deck_list", response.context)
        public_decks = Deck.objects.filter(is_public=True)
        self.assertQuerySetEqual(
            public_decks, response.context["deck_list"], ordered=False
        )

        self.assertNotIn("own_decks", response.context)

    def test_decks_home_authenticated(self):
        """Test the context content for an authenticated user."""
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

    def get_detail_card_list(self, deck: Deck, card_type: Card.Type) -> list[int, Card]:
        """Return the quantity and model of cards of the Deck filtered by their type.

        Args:
            deck (Deck): The deck containing the cards.
            card_type (Card.Type): The type of card to filter.

        Returns:
            list[int, Card]: The list of cards with their amount.
        """
        return [
            (c.quantity, c.card)
            for c in deck.cardindeck_set.all()
            if c.card.type == card_type
        ]

    def assert_deck_detail(self, deck: Deck, response: HttpResponse):
        """Compare the received Deck object with the context on a response returned by
        a view.

        Args:
            deck (Deck): The Deck to compare.
            response (HttpResponse): The response with the context.
        """

        self.assertIn("deck", response.context)
        self.assertEqual(deck, response.context["deck"])
        self.assertIn("character_list", response.context)
        self.assertIn("spell_list", response.context)
        self.assertIn("permanent_list", response.context)
        self.assertListEqual(
            self.get_detail_card_list(deck, Card.Type.CHARACTER),
            response.context["character_list"],
        )
        self.assertListEqual(
            self.get_detail_card_list(deck, Card.Type.SPELL),
            response.context["spell_list"],
        )
        self.assertListEqual(
            self.get_detail_card_list(deck, Card.Type.PERMANENT),
            response.context["permanent_list"],
        )
        self.assertIn("stats", response.context)
        self.assertIn("type_distribution", response.context["stats"])
        self.assertIn("total_count", response.context["stats"])
        self.assertIn("mana_distribution", response.context["stats"])
        self.assertIn("rarity_distribution", response.context["stats"])

    def test_own_public_deck_detail_authenticated(self):
        """Test the deck detail page of an authenticated user to its own public deck."""
        self.client.force_login(self.user)
        public_deck = Deck.objects.filter(is_public=True, owner=self.user).get()
        response = self.client.get(
            reverse("deck-detail", kwargs={"pk": public_deck.id})
        )

        self.assert_deck_detail(public_deck, response)

    def test_other_public_deck_detail_authenticated(self):
        """Test the deck detail page of an unauthenticated user to a public deck."""
        self.client.force_login(self.user)
        public_deck = Deck.objects.filter(is_public=True, owner=self.other_user).get()
        response = self.client.get(
            reverse("deck-detail", kwargs={"pk": public_deck.id})
        )

        self.assert_deck_detail(public_deck, response)

    def test_own_private_deck_detail_authenticated(self):
        """Test the deck detail page of an authenticated user to its own private deck."""
        self.client.force_login(self.user)
        public_deck = Deck.objects.filter(is_public=False, owner=self.user).get()
        response = self.client.get(
            reverse("deck-detail", kwargs={"pk": public_deck.id})
        )

        self.assert_deck_detail(public_deck, response)

    def test_other_private_deck_detail_authenticated(self):
        """Test the deck detail page of an authenticated user to another user's private
        deck.
        """
        self.client.force_login(self.user)
        private_deck = Deck.objects.filter(is_public=False, owner=self.other_user).get()

        response = self.client.get(
            reverse("deck-detail", kwargs={"pk": private_deck.id})
        )
        self.assertTemplateUsed(response, "errors/404.html")

    def test_public_deck_detail_unauthenticated(self):
        """Test the deck detail page of an unauthenticated user to a public deck."""
        public_deck = Deck.objects.filter(is_public=True, owner=self.other_user).get()
        response = self.client.get(
            reverse("deck-detail", kwargs={"pk": public_deck.id})
        )

        self.assert_deck_detail(public_deck, response)

    def test_private_deck_detail_unauthenticated(self):
        """Test the deck detail page of an unauthenticated user to a private deck."""
        private_deck = Deck.objects.filter(is_public=False, owner=self.other_user).get()

        response = self.client.get(
            reverse("deck-detail", kwargs={"pk": private_deck.id})
        )
        self.assertTemplateUsed(response, "errors/404.html")
