from django.contrib.auth.models import User
from django.http import HttpResponse
from django.test import TestCase
from django.urls import reverse

from decks.models import Card, CardInDeck, Deck, Hero
from .utils import generate_card, get_login_url, silence_logging


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
        hero = generate_card(Card.Faction.AXIOM, Card.Type.HERO, Card.Rarity.COMMON)
        character = generate_card(
            Card.Faction.AXIOM, Card.Type.CHARACTER, Card.Rarity.RARE
        )
        spell = generate_card(Card.Faction.AXIOM, Card.Type.SPELL, Card.Rarity.RARE)
        permanent = generate_card(
            Card.Faction.AXIOM, Card.Type.PERMANENT, Card.Rarity.RARE
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

    def test_own_deck_list_unauthenticated(self):
        """Test the view of a user's own decks when requested by an unauthenticated user."""
        response = self.client.get(reverse("own-deck"))

        self.assertRedirects(response, get_login_url("own-deck"), status_code=302)

    def test_own_deck_list(self):
        """Test the view of a user's own decks."""
        self.client.force_login(self.user)
        response = self.client.get(reverse("own-deck"))

        own_decks = Deck.objects.filter(owner=self.user)
        self.assertQuerySetEqual(
            own_decks, response.context["deck_list"], ordered=False
        )

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
        card = CardInDeck.objects.filter(deck=deck)[0].card
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

    def test_card_list_view_unauthenticated(self):
        """Test the view returning all the cards for an unauthenticated user.
        """
        response = self.client.get(reverse("cards"))

        self.assertIn("card_list", response.context)
        cards = Card.objects.filter()
        self.assertQuerySetEqual(cards, response.context["card_list"], ordered=False)
        self.assertNotIn("own_decks", response.context)

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


class DecksFilterViewsTestCase(TestCase):
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
        * 2 Hero
        * 1 Character
        * 1 Spell
        * 1 Permanent
        * 8 Deck
        """
        ax_hero = generate_card(Card.Faction.AXIOM, Card.Type.HERO, Card.Rarity.COMMON)
        mu_hero = generate_card(Card.Faction.MUNA, Card.Type.HERO, Card.Rarity.COMMON)
        character = generate_card(
            Card.Faction.AXIOM, Card.Type.CHARACTER, Card.Rarity.RARE
        )
        spell = generate_card(Card.Faction.AXIOM, Card.Type.SPELL, Card.Rarity.RARE)
        permanent = generate_card(
            Card.Faction.AXIOM, Card.Type.PERMANENT, Card.Rarity.RARE
        )
        cls.user = User.objects.create_user(username=cls.TEST_USER)
        cls.other_user = User.objects.create_user(username=cls.OTHER_TEST_USER)
        cls.create_decks_for_user(cls.user, ax_hero, [character, spell, permanent])
        cls.create_decks_for_user(
            cls.other_user, ax_hero, [character, spell, permanent]
        )
        cls.create_decks_for_user(cls.user, mu_hero, [])
        cls.create_decks_for_user(cls.other_user, mu_hero, [])

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

    def test_decks_home_filters(self):
        """Test the view of all the public Decks after applying filters on the query.
        """
        # Search all the decks with the given name
        response = self.client.get(
            reverse("deck-list") + f"?query={self.PUBLIC_DECK_NAME}"
        )
        query_decks = Deck.objects.filter(is_public=True, name=self.PUBLIC_DECK_NAME)
        self.assertQuerySetEqual(
            query_decks, response.context["deck_list"], ordered=False
        )

        # Search all the decks with a string not appearing in any Deck's name
        response = self.client.get(reverse("deck-list") + "?query=XX")
        public_decks = Deck.objects.filter(is_public=True, name="XX")
        self.assertQuerySetEqual(
            public_decks, response.context["deck_list"], ordered=False
        )

        # Search all the decks belonging to the AXIOM faction
        response = self.client.get(reverse("deck-list") + "?faction=AX")
        axiom_decks = Deck.objects.filter(
            is_public=True, hero__faction=Card.Faction.AXIOM
        )
        self.assertQuerySetEqual(
            axiom_decks, response.context["deck_list"], ordered=False
        )

        # Search all the decks belonging to either the AXIOM or MUNA factions
        response = self.client.get(reverse("deck-list") + "?faction=AX,MU")
        multifaction_decks = Deck.objects.filter(
            is_public=True, hero__faction__in=[Card.Faction.AXIOM, Card.Faction.MUNA]
        )
        self.assertQuerySetEqual(
            multifaction_decks, response.context["deck_list"], ordered=False
        )

        # Search all the decks belonging to an invalid faction (parameter ignored)
        response = self.client.get(reverse("deck-list") + "?faction=XX")
        public_decks = Deck.objects.filter(is_public=True)
        self.assertQuerySetEqual(
            public_decks, response.context["deck_list"], ordered=False
        )

        # Search all the decks with an invalid legality (parameter ignored)
        response = self.client.get(reverse("deck-list") + "?legality=XX")
        public_decks = Deck.objects.filter(is_public=True)
        self.assertQuerySetEqual(
            public_decks, response.context["deck_list"], ordered=False
        )

        # Search all the decks with an invalid "other" filter (parameter ignored)
        response = self.client.get(reverse("deck-list") + "?other=XX")
        public_decks = Deck.objects.filter(is_public=True)
        self.assertQuerySetEqual(
            public_decks, response.context["deck_list"], ordered=False
        )
