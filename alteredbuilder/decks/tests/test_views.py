import uuid

from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.urls import reverse

from decks.models import Card, Deck, PrivateLink
from .utils import (
    BaseViewTestCase,
    generate_card,
    get_detail_card_list,
    get_login_url,
    silence_logging,
)


class DeckListViewTestCase(BaseViewTestCase):
    """Test case focusing on the main Deck ListView."""

    @classmethod
    def setUpTestData(cls):
        """Create the database data for this test.

        Specifically, it creates what `BaseViewTestCase` does and adds:
        * 1 Hero
        * 4 Deck
        """
        super(DeckListViewTestCase, cls).setUpTestData()
        mu_hero = generate_card(Card.Faction.MUNA, Card.Type.HERO, Card.Rarity.COMMON)
        cls.create_decks_for_user(cls.user, mu_hero, [])
        cls.create_decks_for_user(cls.other_user, mu_hero, [])

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

    def test_deck_list_filters(self):
        """Test the view of all the public Decks after applying filters on the query."""
        # Search all the decks with the given name
        response = self.client.get(
            reverse("deck-list") + f"?query={self.PUBLIC_DECK_NAME}"
        )
        query_decks = Deck.objects.filter(is_public=True, name=self.PUBLIC_DECK_NAME)
        self.assertQuerySetEqual(
            query_decks, response.context["deck_list"], ordered=False
        )

        # Search all the decks with a string not appearing in any Deck's name
        response = self.client.get(reverse("deck-list") + "?query=XXXX")
        query_decks = Deck.objects.none()
        self.assertQuerySetEqual(
            query_decks, response.context["deck_list"], ordered=False
        )

        # Search all the decks belonging to the AXIOM faction
        response = self.client.get(reverse("deck-list") + "?faction=AX")
        query_decks = Deck.objects.filter(
            is_public=True, hero__faction=Card.Faction.AXIOM
        )
        self.assertQuerySetEqual(
            query_decks, response.context["deck_list"], ordered=False
        )

        # Search all the decks belonging to either the AXIOM or MUNA factions
        response = self.client.get(reverse("deck-list") + "?faction=AX,MU")
        query_decks = Deck.objects.filter(
            is_public=True, hero__faction__in=[Card.Faction.AXIOM, Card.Faction.MUNA]
        )
        self.assertQuerySetEqual(
            query_decks, response.context["deck_list"], ordered=False
        )

        # Search all the decks belonging to an invalid faction (parameter ignored)
        response = self.client.get(reverse("deck-list") + "?faction=XXXX")
        query_decks = Deck.objects.filter(is_public=True)
        self.assertQuerySetEqual(
            query_decks, response.context["deck_list"], ordered=False
        )

        # Search all the decks with an invalid legality (parameter ignored)
        response = self.client.get(reverse("deck-list") + "?legality=XXXX")
        query_decks = Deck.objects.filter(is_public=True)
        self.assertQuerySetEqual(
            query_decks, response.context["deck_list"], ordered=False
        )

        # Search all the decks with an invalid "other" filter (parameter ignored)
        response = self.client.get(reverse("deck-list") + "?other=XXXX")
        query_decks = Deck.objects.filter(is_public=True)
        self.assertQuerySetEqual(
            query_decks, response.context["deck_list"], ordered=False
        )


class DeckDetailViewTestCase(BaseViewTestCase):
    """Test case focusing on the Deck DetailView."""

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
            get_detail_card_list(deck, Card.Type.CHARACTER),
            response.context["character_list"],
        )
        self.assertListEqual(
            get_detail_card_list(deck, Card.Type.SPELL), response.context["spell_list"]
        )
        self.assertListEqual(
            get_detail_card_list(deck, Card.Type.PERMANENT),
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


class OwnDeckListViewTestCase(BaseViewTestCase):
    """Test case focusing on the Deck ListView of a user's own decks."""

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


class CardListViewTestCase(BaseViewTestCase):
    """Test case focusing on the Card ListView."""

    def test_card_list_view_unauthenticated(self):
        """Test the view returning all the cards for an unauthenticated user."""
        response = self.client.get(reverse("cards"))

        self.assertIn("card_list", response.context)
        cards = Card.objects.all()
        self.assertQuerySetEqual(cards, response.context["card_list"], ordered=False)
        self.assertNotIn("own_decks", response.context)

    def test_card_list_filters(self):
        """Test the view of all the Cards after applying filters on the query."""
        generate_card(Card.Faction.AXIOM, Card.Type.PERMANENT, Card.Rarity.COMMON)
        generate_card(Card.Faction.MUNA, Card.Type.CHARACTER, Card.Rarity.RARE)

        card = Card.objects.first()
        # Search all the decks with the given name
        response = self.client.get(reverse("cards") + f"?query={card.name}")
        query_cards = Card.objects.filter(name=card.name)
        self.assertQuerySetEqual(
            query_cards, response.context["card_list"], ordered=False
        )

        # Search all the cards with a string not appearing in any Card's name
        response = self.client.get(reverse("cards") + "?query=XXXX")
        query_cards = Card.objects.none()
        self.assertQuerySetEqual(
            query_cards, response.context["card_list"], ordered=False
        )

        # Search all the cards belonging to the AXIOM faction
        response = self.client.get(reverse("cards") + "?faction=AX")
        query_cards = Card.objects.filter(faction=Card.Faction.AXIOM)
        self.assertQuerySetEqual(
            query_cards, response.context["card_list"], ordered=False
        )

        # Search all the cards belonging to either the AXIOM or MUNA factions
        response = self.client.get(reverse("cards") + "?faction=AX,MU")
        query_cards = Card.objects.filter(
            faction__in=[Card.Faction.AXIOM, Card.Faction.MUNA]
        )
        self.assertQuerySetEqual(
            query_cards, response.context["card_list"], ordered=False
        )

        # Search all the cards belonging to an invalid faction (parameter ignored)
        response = self.client.get(reverse("cards") + "?faction=XXXX")
        query_cards = Card.objects.all()
        self.assertQuerySetEqual(
            query_cards, response.context["card_list"], ordered=False
        )

        # Search all the cards with the COMMON rarity
        response = self.client.get(reverse("cards") + "?rarity=C")
        query_cards = Card.objects.filter(rarity=Card.Rarity.COMMON)
        self.assertQuerySetEqual(
            query_cards, response.context["card_list"], ordered=False
        )

        # Search all the cards with the COMMON or RARE rarities
        response = self.client.get(reverse("cards") + "?rarity=C,R")
        query_cards = Card.objects.filter(
            rarity__in=[Card.Rarity.COMMON, Card.Rarity.RARE]
        )
        self.assertQuerySetEqual(
            query_cards, response.context["card_list"], ordered=False
        )

        # Search all the cards with an invalid rarity (parameter ignored)
        response = self.client.get(reverse("cards") + "?rarity=XXXXX")
        query_cards = Card.objects.all()
        self.assertQuerySetEqual(
            query_cards, response.context["card_list"], ordered=False
        )

        # Search all the cards of type CHARACTER
        response = self.client.get(reverse("cards") + "?type=character")
        query_cards = Card.objects.filter(type=Card.Type.CHARACTER)
        self.assertQuerySetEqual(
            query_cards, response.context["card_list"], ordered=False
        )

        # Search all the cards of type CHARACTER or PERMANENT
        response = self.client.get(reverse("cards") + "?type=character,permanent")
        query_cards = Card.objects.filter(
            type__in=[Card.Type.CHARACTER, Card.Type.PERMANENT]
        )
        self.assertQuerySetEqual(
            query_cards, response.context["card_list"], ordered=False
        )

        # Search all the cards of type CHARACTER
        response = self.client.get(reverse("cards") + "?type=XXXX")
        query_cards = Card.objects.all()
        self.assertQuerySetEqual(
            query_cards, response.context["card_list"], ordered=False
        )

        # Search all the cards by RARITY order
        response = self.client.get(reverse("cards") + "?order=rarity")
        query_cards = Card.objects.order_by("rarity", "reference")
        self.assertQuerySetEqual(query_cards, response.context["card_list"])

        # Search all the cards by RESERVE MANA order
        response = self.client.get(reverse("cards") + "?order=reserve")
        query_cards = Card.objects.order_by(
            Coalesce(
                "character__recall_cost", "spell__recall_cost", "permanent__recall_cost"
            ),
            "reference",
        )
        self.assertQuerySetEqual(query_cards, response.context["card_list"])

        # Search all the cards by inverse MANA order
        response = self.client.get(reverse("cards") + "?order=-mana")
        query_cards = Card.objects.order_by(
            Coalesce(
                "character__main_cost", "spell__main_cost", "permanent__main_cost"
            ).desc(),
            "-reference",
        )
        self.assertQuerySetEqual(query_cards, response.context["card_list"])

        # Search all the COMMON CHARACTERS or PERMANENTS of AXIOM ordered by inverse NAME order
        response = self.client.get(
            reverse("cards")
            + "?faction=AX&rarity=C&type=character,permanent&order=-name"
        )
        query_cards = Card.objects.filter(
            faction=Card.Faction.AXIOM,
            rarity=Card.Rarity.COMMON,
            type__in=[Card.Type.CHARACTER, Card.Type.PERMANENT],
        ).order_by("-name", "-reference")
        self.assertQuerySetEqual(query_cards, response.context["card_list"])


class AccessPrivateLinkViewTestCase(BaseViewTestCase):
    """Test case focusing on the view to access a Deck through a PrivateLink."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.pl_deck = Deck.objects.filter(owner=cls.user, is_public=False).first()
        cls.pl = PrivateLink.objects.create(deck=cls.pl_deck)

    def test_unauthenticated(self):
        """Test the view of a Deck through a PrivateLink when requested by an
        unauthenticated user.
        """
        url = reverse(
            "private-url-deck-detail",
            kwargs={"pk": self.pl_deck.id, "code": self.pl.code},
        )
        response = self.client.get(url)

        self.assertRedirects(response, get_login_url(next=url), status_code=302)

    def test_authenticated_deck_mismatch(self):
        """Test the view of a Deck through a PrivateLink when requested by an
        authenticated user, but the deck id does not correspond to the code.
        """
        another_deck = (
            Deck.objects.filter(is_public=False)
            .exclude(id__in=[self.pl_deck.id])
            .first()
        )
        url = reverse(
            "private-url-deck-detail",
            kwargs={"pk": another_deck.id, "code": self.pl.code},
        )
        self.client.force_login(self.other_user)
        response = self.client.get(url)

        self.assertTemplateUsed(response, "errors/404.html")

    def test_authenticated_code_mismatch(self):
        """Test the view of a Deck through a PrivateLink when requested by an
        authenticated user, but the code does not correspond to the deck.
        """
        code = str(uuid.uuid4())
        url = reverse(
            "private-url-deck-detail",
            kwargs={"pk": self.pl_deck.id, "code": code},
        )
        self.client.force_login(self.other_user)
        response = self.client.get(url)

        self.assertTemplateUsed(response, "errors/404.html")

    def test_authenticated_by_another_user(self):
        """Test the view of a Deck through a PrivateLink when requested by an
        authenticated user other than the owner.
        """
        self.client.force_login(self.other_user)
        response = self.client.get(
            reverse(
                "private-url-deck-detail",
                kwargs={"pk": self.pl_deck.id, "code": self.pl.code},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed("decks/deck_detail.html")

    def test_authenticated_by_owner(self):
        """Test the view of a Deck through a PrivateLink when requested by the owner."""
        self.client.force_login(self.user)
        response = self.client.get(
            reverse(
                "private-url-deck-detail",
                kwargs={"pk": self.pl_deck.id, "code": self.pl.code},
            )
        )

        self.assertRedirects(
            response,
            reverse("deck-detail", kwargs={"pk": self.pl_deck.id}),
            status_code=302,
        )

    def test_authenticated_to_public_deck(self):
        """Test the view of a public Deck through a PrivateLink."""
        public_deck = Deck.objects.filter(owner=self.other_user, is_public=True).first()
        pl = PrivateLink.objects.create(deck=public_deck)

        self.client.force_login(self.user)
        response = self.client.get(
            reverse(
                "private-url-deck-detail",
                kwargs={"pk": public_deck.id, "code": pl.code},
            )
        )

        self.assertRedirects(
            response,
            reverse("deck-detail", kwargs={"pk": public_deck.id}),
            status_code=302,
        )


class CreatePrivateLinkViewTestCase(BaseViewTestCase):
    """Test case focusing on the view that creates a PrivateLink for a Deck."""

    def assert_ajax_error(
        self, response: HttpResponse, status_code: int, error_message: str
    ) -> None:
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
        """Test the view to create a PrivateLink for a Deck. It currently works via an AJAX
        call.

        Throughout this method, multiple times the logging is silenced, otherwise the
        logs for a failed/invalid request would be logged to the console and would mess
        with the unittest expected logs.
        """
        deck = Deck.objects.get(owner=self.user, name=self.PRIVATE_DECK_NAME)
        test_url = reverse("create-private-link", kwargs={"pk": deck.id})
        headers = {
            "HTTP_X_REQUESTED_WITH": "XMLHttpRequest",
            "content_type": "application/json",
        }

        # Test an unauthenticated client
        response = self.client.post(test_url)
        self.assertRedirects(response, get_login_url(next=test_url), status_code=302)

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

        # Test a request targeting a non-existent deck id
        wrong_url = reverse("create-private-link", kwargs={"pk": 100_000})
        with silence_logging():
            response = self.client.post(wrong_url, **headers)
        self.assert_ajax_error(response, 404, "Deck not found")

        # Test a request with valid data
        response = self.client.post(test_url, **headers)

        pl = PrivateLink.objects.get(deck=deck)
        response_data = response.json()["data"]
        created_url = reverse(
            "private-url-deck-detail", kwargs={"pk": deck.id, "code": pl.code}
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response_data["created"])
        self.assertEqual(response_data["link"], created_url)

        # Test a request with valid data, which will not create the link
        response = self.client.post(test_url, **headers)

        pl.refresh_from_db()
        created_url = reverse(
            "private-url-deck-detail", kwargs={"pk": deck.id, "code": pl.code}
        )
        response_data = response.json()["data"]
        self.assertEqual(response.status_code, 201)
        self.assertFalse(response_data["created"])
        self.assertEqual(response_data["link"], created_url)
        self.assertEqual(PrivateLink.objects.filter(deck=deck).count(), 1)

        # Test a request with valid data and a public deck
        public_deck = Deck.objects.filter(owner=self.user, is_public=True).first()
        wrong_url = reverse("create-private-link", kwargs={"pk": public_deck.id})
        with silence_logging():
            response = self.client.post(wrong_url, **headers)

        self.assert_ajax_error(response, 400, "Invalid request")
        self.assertFalse(PrivateLink.objects.filter(deck=public_deck).exists())

        # Test a request with valid data and a not-owned deck
        not_owned_deck = Deck.objects.filter(
            owner=self.other_user, is_public=False
        ).first()
        wrong_url = reverse("create-private-link", kwargs={"pk": not_owned_deck.id})
        with silence_logging():
            response = self.client.post(wrong_url, **headers)

        self.assert_ajax_error(response, 404, "Deck not found")
        self.assertFalse(PrivateLink.objects.filter(deck=not_owned_deck).exists())
