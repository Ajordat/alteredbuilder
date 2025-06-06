from http import HTTPStatus
from urllib.parse import quote
import uuid

from django.db.models import Exists, OuterRef, Q
from django.http import HttpResponse
from django.urls import reverse

from config.tests.utils import get_login_url, silence_logging
from decks.models import Card, CardInDeck, Deck, LovePoint, PrivateLink, Subtype
from decks.tests.utils import (
    AjaxTestCase,
    BaseViewTestCase,
    generate_card,
    get_detail_card_list,
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

        url = reverse("deck-list")

        # Search all the decks with the given name
        filter = f"?query={self.PUBLIC_DECK_NAME}"
        with self.subTest(filter=filter):
            response = self.client.get(url + filter)
            query_decks = Deck.objects.filter(
                is_public=True, name=self.PUBLIC_DECK_NAME
            )
            self.assertQuerySetEqual(
                query_decks, response.context["deck_list"], ordered=False
            )

        # Search all the decks with a string not appearing in any Deck's name
        filter = "?query=XXXX"
        with self.subTest(filter=filter):
            response = self.client.get(url + filter)
            query_decks = Deck.objects.none()
            self.assertQuerySetEqual(
                query_decks, response.context["deck_list"], ordered=False
            )

        # Search all the decks belonging to the AXIOM faction
        filter = "?faction=AX"
        with self.subTest(filter=filter):
            response = self.client.get(url + filter)
            query_decks = Deck.objects.filter(
                is_public=True, hero__faction=Card.Faction.AXIOM
            )
            self.assertQuerySetEqual(
                query_decks, response.context["deck_list"], ordered=False
            )

        # Search all the decks belonging to either the AXIOM or MUNA factions
        filter = "?faction=AX,MU"
        with self.subTest(filter=filter):
            response = self.client.get(url + filter)
            query_decks = Deck.objects.filter(
                is_public=True,
                hero__faction__in=[Card.Faction.AXIOM, Card.Faction.MUNA],
            )
            self.assertQuerySetEqual(
                query_decks, response.context["deck_list"], ordered=False
            )

        # Search all the decks belonging to an invalid faction (parameter ignored)
        filter = "?faction=XXXX"
        with self.subTest(filter=filter):
            response = self.client.get(url + filter)
            query_decks = Deck.objects.filter(is_public=True)
            self.assertQuerySetEqual(
                query_decks, response.context["deck_list"], ordered=False
            )

        # Search all the decks that are legal on the Exalts format
        filter = "?legality=exalts"
        with self.subTest(filter=filter):
            response = self.client.get(url + filter)
            query_decks = Deck.objects.filter(is_public=True, is_exalts_legal=True)
            self.assertQuerySetEqual(
                query_decks, response.context["deck_list"], ordered=False
            )

        # Search all the decks that are legal on the Draft format
        filter = "?legality=draft"
        with self.subTest(filter=filter):
            response = self.client.get(url + filter)
            query_decks = Deck.objects.filter(is_public=True, is_draft_legal=True)
            self.assertQuerySetEqual(
                query_decks, response.context["deck_list"], ordered=False
            )

        # Search all the decks that are legal on the Standard or Draft formats
        filter = "?legality=standard,draft"
        with self.subTest(filter=filter):
            response = self.client.get(url + filter)
            query_decks = Deck.objects.filter(is_public=True, is_standard_legal=True)
            self.assertQuerySetEqual(
                query_decks, response.context["deck_list"], ordered=False
            )

        # Search all the decks with an invalid legality (parameter ignored)
        filter = "?legality=XXXX"
        with self.subTest(filter=filter):
            response = self.client.get(url + filter)
            query_decks = Deck.objects.filter(is_public=True)
            self.assertQuerySetEqual(
                query_decks, response.context["deck_list"], ordered=False
            )

        # Search all the loved decks with an unauthenticated user (parameter ignored)
        filter = "?other=loved"
        with self.subTest(filter=filter):
            response = self.client.get(url + filter)
            query_decks = Deck.objects.filter(is_public=True)
            self.assertQuerySetEqual(
                query_decks, response.context["deck_list"], ordered=False
            )

        # Search all the loved decks
        filter = "?other=loved"
        self.client.force_login(self.user)
        with self.subTest(filter=filter):
            response = self.client.get(url + filter)
            lp = LovePoint.objects.filter(user=self.user).values_list(
                "deck_id", flat=True
            )
            query_decks = Deck.objects.filter(is_public=True, id__in=lp)
            self.assertQuerySetEqual(
                query_decks, response.context["deck_list"], ordered=False
            )
        self.client.logout()

        # Search all the decks with an invalid "other" filter (parameter ignored)
        filter = "?other=XXXX"
        with self.subTest(filter=filter):
            response = self.client.get(url + filter)
            query_decks = Deck.objects.filter(is_public=True)
            self.assertQuerySetEqual(
                query_decks, response.context["deck_list"], ordered=False
            )

    def test_deck_list_u_advanced_filters(self):
        """Test the view of all the public Decks after filtering the query by user."""
        # Search all the decks with the given name
        deck = Deck.objects.filter(is_public=True).first()
        response = self.client.get(
            reverse("deck-list") + f"?query=u:{deck.owner.username}"
        )

        query_decks = Deck.objects.filter(
            is_public=True, owner__username__iexact=deck.owner.username
        )
        self.assertQuerySetEqual(
            query_decks, response.context["deck_list"], ordered=False
        )

    def test_deck_list_h_advanced_filters(self):
        """Test the view of all the public Decks after filtering the query by hero."""
        # Search all the decks with the given name
        deck = Deck.objects.filter(is_public=True, hero__isnull=False).first()

        response = self.client.get(
            reverse("deck-list") + f"?query=h:{deck.hero.name.split(" ")[-1]}"
        )

        query_decks = Deck.objects.filter(
            is_public=True, hero__name__icontains=deck.hero.name
        )
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
            get_detail_card_list(deck, Card.Type.LANDMARK_PERMANENT),
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
        response = self.client.get(public_deck.get_absolute_url())

        self.assert_deck_detail(public_deck, response)

    def test_other_public_deck_detail_authenticated(self):
        """Test the deck detail page of an unauthenticated user to a public deck."""
        self.client.force_login(self.user)
        public_deck = Deck.objects.filter(is_public=True, owner=self.other_user).get()
        response = self.client.get(public_deck.get_absolute_url())

        self.assert_deck_detail(public_deck, response)

    def test_own_private_deck_detail_authenticated(self):
        """Test the deck detail page of an authenticated user to its own private deck."""
        self.client.force_login(self.user)
        public_deck = Deck.objects.filter(is_public=False, owner=self.user).get()
        response = self.client.get(public_deck.get_absolute_url())

        self.assert_deck_detail(public_deck, response)

    def test_other_private_deck_detail_authenticated(self):
        """Test the deck detail page of an authenticated user to another user's private
        deck.
        """
        self.client.force_login(self.user)
        private_deck = Deck.objects.filter(is_public=False, owner=self.other_user).get()

        with silence_logging():
            response = self.client.get(private_deck.get_absolute_url())

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, "errors/404.html")

    def test_public_deck_detail_unauthenticated(self):
        """Test the deck detail page of an unauthenticated user to a public deck."""
        public_deck = Deck.objects.filter(is_public=True, owner=self.other_user).get()
        response = self.client.get(public_deck.get_absolute_url())

        self.assert_deck_detail(public_deck, response)

    def test_private_deck_detail_unauthenticated(self):
        """Test the deck detail page of an unauthenticated user to a private deck."""
        private_deck = Deck.objects.filter(is_public=False, owner=self.other_user).get()
        with silence_logging():
            response = self.client.get(private_deck.get_absolute_url())

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, "errors/404.html")


class OwnDeckListViewTestCase(BaseViewTestCase):
    """Test case focusing on the Deck ListView of a user's own decks."""

    def test_own_deck_list_unauthenticated(self):
        """Test the view of a user's own decks when requested by an unauthenticated user."""
        response = self.client.get(reverse("own-deck"))

        self.assertRedirects(
            response, get_login_url("own-deck"), status_code=HTTPStatus.FOUND
        )

    def test_own_deck_list(self):
        """Test the view of a user's own decks."""
        self.client.force_login(self.user)
        response = self.client.get(reverse("own-deck"))

        own_decks = Deck.objects.filter(owner=self.user)
        self.assertQuerySetEqual(
            own_decks, response.context["deck_list"], ordered=False
        )

    def test_context_own_deck_list(self):
        # Get the only hero
        first_axiom = Card.objects.filter(type=Card.Type.HERO).first()
        # Create more heroes
        second_axiom = generate_card(Card.Faction.AXIOM, Card.Type.HERO)
        only_lyra_hero = generate_card(Card.Faction.LYRA, Card.Type.HERO)

        expected_heroes_data: dict[str, list[str]] = {
            "Axiom": [first_axiom.name, second_axiom.name],
            "Bravos": [],
            "Lyra": [only_lyra_hero.name],
            "Muna": [],
            "Ordis": [],
            "Yzmir": [],
        }

        self.client.force_login(self.user)
        response = self.client.get(reverse("own-deck"))

        assert response.context["factions_heroes"] == expected_heroes_data


class CardListViewTestCase(BaseViewTestCase):
    """Test case focusing on the Card ListView."""

    def test_card_list_view_unauthenticated(self):
        """Test the view returning all the cards for an unauthenticated user."""
        response = self.client.get(reverse("cards"))

        self.assertIn("card_list", response.context)
        cards = Card.objects.all()
        self.assertQuerySetEqual(cards, response.context["card_list"], ordered=False)
        self.assertNotIn("own_decks", response.context)

    def test_card_list_view_authenticated(self):
        """Test the view returning all the cards for an authenticated user."""
        self.client.force_login(self.user)
        response = self.client.get(reverse("cards"))

        self.assertIn("card_list", response.context)
        cards = Card.objects.all()
        self.assertQuerySetEqual(cards, response.context["card_list"], ordered=False)

        self.assertIn("own_decks", response.context)
        decks = (
            Deck.objects.filter(owner=self.user)
            .values("id", "name", "hero__faction")
            .order_by("-modified_at")
        )
        self.assertQuerySetEqual(decks, response.context["own_decks"])

    def test_card_list_view_authenticated_with_not_owned_deck(self):
        """Test the view returning all the cards for an authenticated user that wants
        to edit a deck that isn't owned by them (parameter is ignored)."""
        deck = Deck.objects.exclude(owner=self.user).first()
        self.client.force_login(self.user)
        response = self.client.get(reverse("cards") + f"?deck={deck.id}")

        self.assertIn("card_list", response.context)
        cards = Card.objects.all()
        self.assertQuerySetEqual(cards, response.context["card_list"], ordered=False)

        self.assertIn("own_decks", response.context)
        decks = (
            Deck.objects.filter(owner=self.user)
            .values("id", "name", "hero__faction")
            .order_by("-modified_at")
        )
        self.assertQuerySetEqual(decks, response.context["own_decks"])

        self.assertNotIn("edit_deck", response.context)

    def test_card_list_view_authenticated_with_owned_deck(self):
        """Test the view returning all the cards for an authenticated user that wants
        to edit a deck that is owned by them."""
        deck = Deck.objects.filter(owner=self.user).first()
        self.client.force_login(self.user)
        response = self.client.get(reverse("cards") + f"?deck={deck.id}")

        self.assertIn("card_list", response.context)
        cards = Card.objects.all()
        self.assertQuerySetEqual(cards, response.context["card_list"], ordered=False)

        self.assertIn("own_decks", response.context)
        decks = (
            Deck.objects.filter(owner=self.user)
            .values("id", "name", "hero__faction")
            .order_by("-modified_at")
        )
        self.assertQuerySetEqual(decks, response.context["own_decks"])

        self.assertIn("edit_deck", response.context)
        self.assertEqual(deck, response.context["edit_deck"])

        self.assertIn("character_cards", response.context)
        cid = CardInDeck.objects.filter(deck=deck, card__type=Card.Type.CHARACTER)
        self.assertQuerySetEqual(
            cid, response.context["character_cards"], ordered=False
        )

        self.assertIn("spell_cards", response.context)
        cid = CardInDeck.objects.filter(deck=deck, card__type=Card.Type.SPELL)
        self.assertQuerySetEqual(cid, response.context["spell_cards"], ordered=False)

        self.assertIn("permanent_cards", response.context)
        cid = CardInDeck.objects.filter(
            deck=deck, card__type=Card.Type.LANDMARK_PERMANENT
        )
        self.assertQuerySetEqual(
            cid, response.context["permanent_cards"], ordered=False
        )

    def test_card_list_filters(self):
        """Test the view of all the Cards after applying filters on the query."""
        generate_card(
            Card.Faction.AXIOM, Card.Type.LANDMARK_PERMANENT, Card.Rarity.COMMON
        )
        generate_card(Card.Faction.MUNA, Card.Type.CHARACTER, Card.Rarity.RARE)

        card = Card.objects.first()
        url = reverse("cards")

        # Search all the decks with the given name
        filter = f"?query={card.name}"
        with self.subTest(filter=filter):
            response = self.client.get(url + filter)
            query_cards = Card.objects.filter(name=card.name)
            self.assertQuerySetEqual(
                query_cards, response.context["card_list"], ordered=False
            )

        # Search all the cards with a string not appearing in any Card's name
        filter = "?query=XXXX"
        with self.subTest(filter=filter):
            response = self.client.get(url + filter)
            query_cards = Card.objects.none()
            self.assertQuerySetEqual(
                query_cards, response.context["card_list"], ordered=False
            )

        # Search all the cards belonging to the AXIOM faction
        filter = "?faction=AX"
        with self.subTest(filter=filter):
            response = self.client.get(url + filter)
            query_cards = Card.objects.filter(faction=Card.Faction.AXIOM)
            self.assertQuerySetEqual(
                query_cards, response.context["card_list"], ordered=False
            )

        # Search all the cards belonging to either the AXIOM or MUNA factions
        filter = "?faction=AX,MU"
        with self.subTest(filter=filter):
            response = self.client.get(url + filter)
            query_cards = Card.objects.filter(
                faction__in=[Card.Faction.AXIOM, Card.Faction.MUNA]
            )
            self.assertQuerySetEqual(
                query_cards, response.context["card_list"], ordered=False
            )

        # Search all the cards belonging to an invalid faction (parameter ignored)
        filter = "?faction=XXXX"
        with self.subTest(filter=filter):
            response = self.client.get(url + filter)
            query_cards = Card.objects.all()
            self.assertQuerySetEqual(
                query_cards, response.context["card_list"], ordered=False
            )

        # Search all the cards with the COMMON rarity
        filter = "?rarity=C"
        with self.subTest(filter=filter):
            response = self.client.get(url + filter)
            query_cards = Card.objects.filter(rarity=Card.Rarity.COMMON)
            self.assertQuerySetEqual(
                query_cards, response.context["card_list"], ordered=False
            )

        # Search all the cards with the COMMON or RARE rarities
        filter = "?rarity=C,R"
        with self.subTest(filter=filter):
            response = self.client.get(url + filter)
            query_cards = Card.objects.filter(
                rarity__in=[Card.Rarity.COMMON, Card.Rarity.RARE]
            )
            self.assertQuerySetEqual(
                query_cards, response.context["card_list"], ordered=False
            )

        # Search all the cards with an invalid rarity (parameter ignored)
        filter = "?rarity=XXXXX"
        with self.subTest(filter=filter):
            response = self.client.get(url + filter)
            query_cards = Card.objects.all()
            self.assertQuerySetEqual(
                query_cards, response.context["card_list"], ordered=False
            )

        # Search all the cards of type CHARACTER
        filter = "?type=character"
        with self.subTest(filter=filter):
            response = self.client.get(url + filter)
            query_cards = Card.objects.filter(type=Card.Type.CHARACTER)
            self.assertQuerySetEqual(
                query_cards, response.context["card_list"], ordered=False
            )

        # Search all the cards of type CHARACTER or PERMANENT
        filter = "?type=character,landmark_permanent"
        with self.subTest(filter=filter):
            response = self.client.get(url + filter)
            query_cards = Card.objects.filter(
                type__in=[Card.Type.CHARACTER, Card.Type.LANDMARK_PERMANENT]
            )
            self.assertQuerySetEqual(
                query_cards, response.context["card_list"], ordered=False
            )

        # Search all the cards of type CHARACTER
        filter = "?type=XXXX"
        with self.subTest(filter=filter):
            response = self.client.get(url + filter)
            query_cards = Card.objects.all()
            self.assertQuerySetEqual(
                query_cards, response.context["card_list"], ordered=False
            )

        # Search all the cards by RARITY order
        filter = "?order=rarity"
        with self.subTest(filter=filter):
            response = self.client.get(url + filter)
            query_cards = Card.objects.order_by("rarity", "reference")
            self.assertQuerySetEqual(query_cards, response.context["card_list"])

        # Search all the cards by RESERVE MANA order
        filter = "?order=reserve"
        with self.subTest(filter=filter):
            response = self.client.get(url + filter)
            query_cards = Card.objects.exclude(type=Card.Type.HERO).order_by(
                "stats__recall_cost", "reference"
            )
            self.assertQuerySetEqual(query_cards, response.context["card_list"])

        # Search all the cards by inverse MANA order
        filter = "?order=-mana"
        with self.subTest(filter=filter):
            response = self.client.get(url + filter)
            query_cards = Card.objects.exclude(type=Card.Type.HERO).order_by(
                "-stats__main_cost", "-reference"
            )
            self.assertQuerySetEqual(query_cards, response.context["card_list"])

        # Search all the COMMON CHARACTERS or PERMANENTS of AXIOM ordered by inverse
        # NAME order
        filter = "?faction=AX&rarity=C&type=character,landmark_permanent&order=-name"
        with self.subTest(filter=filter):
            response = self.client.get(url + filter)
            query_cards = Card.objects.filter(
                faction=Card.Faction.AXIOM,
                rarity=Card.Rarity.COMMON,
                type__in=[Card.Type.CHARACTER, Card.Type.LANDMARK_PERMANENT],
            ).order_by("-name", "-reference")
            self.assertQuerySetEqual(query_cards, response.context["card_list"])

    def test_card_list_hc_advanced_filters(self):
        """Test the view of all the Cards after applying advanced filters on the query."""

        url = reverse("cards")

        # Search all the cards with a hand cost of 2
        value = 2
        filter = f"?query={quote('hc=')}{value}"
        with self.subTest(filter=filter):
            response = self.client.get(url + filter)
            query_cards = Card.objects.filter(stats__main_cost=value)
            self.assertQuerySetEqual(
                query_cards, response.context["card_list"], ordered=False
            )

        # Search all the cards with a hand cost greater than 2
        value = 2
        filter = f"?query={quote('hc>')}{value}"
        with self.subTest(filter=filter):
            response = self.client.get(url + filter)
            query_cards = Card.objects.filter(stats__main_cost__gt=value)
            self.assertQuerySetEqual(
                query_cards, response.context["card_list"], ordered=False
            )

        # Search all the cards with a hand cost greater than or equal to 2
        value = 2
        filter = f"?query={quote('hc>=')}{value}"
        with self.subTest(filter=filter):
            response = self.client.get(url + filter)
            query_cards = Card.objects.filter(stats__main_cost__gte=value)
            self.assertQuerySetEqual(
                query_cards, response.context["card_list"], ordered=False
            )

        # Search all the cards with a hand cost smaller than 4
        value = 4
        filter = f"?query={quote('hc<')}{value}"
        with self.subTest(filter=filter):
            response = self.client.get(url + filter)
            query_cards = Card.objects.filter(stats__main_cost__lt=value)
            self.assertQuerySetEqual(
                query_cards, response.context["card_list"], ordered=False
            )

        # Search all the cards with a hand cost smaller than or equal to 4
        value = 4
        filter = f"?query={quote('hc<=')}{value}"
        with self.subTest(filter=filter):
            response = self.client.get(url + filter)
            query_cards = Card.objects.filter(stats__main_cost__lte=value)
            self.assertQuerySetEqual(
                query_cards, response.context["card_list"], ordered=False
            )

    def test_card_list_rc_advanced_filters(self):
        """Test the view of all the Cards after applying advanced filters on the query."""

        url = reverse("cards")

        # Search all the cards with a reserve cost of 2
        value = 2
        filter = f"?query={quote('rc=')}{value}"
        with self.subTest(filter=filter):
            response = self.client.get(url + filter)
            query_cards = Card.objects.filter(stats__recall_cost=value)
            self.assertQuerySetEqual(
                query_cards, response.context["card_list"], ordered=False
            )

        # Search all the cards with a reserve cost greater than 2
        value = 2
        filter = f"?query={quote('rc>')}{value}"
        with self.subTest(filter=filter):
            response = self.client.get(url + filter)
            query_cards = Card.objects.filter(stats__recall_cost__gt=value)
            self.assertQuerySetEqual(
                query_cards, response.context["card_list"], ordered=False
            )

        # Search all the cards with a reserve cost greater than or equal to 2
        value = 2
        filter = f"?query={quote('rc>=')}{value}"
        with self.subTest(filter=filter):
            response = self.client.get(url + filter)
            query_cards = Card.objects.filter(stats__recall_cost__gte=value)
            self.assertQuerySetEqual(
                query_cards, response.context["card_list"], ordered=False
            )

        # Search all the cards with a reserve cost smaller than 4
        value = 4
        filter = f"?query={quote('rc<')}{value}"
        with self.subTest(filter=filter):
            response = self.client.get(url + filter)
            query_cards = Card.objects.filter(stats__recall_cost__lt=value)
            self.assertQuerySetEqual(
                query_cards, response.context["card_list"], ordered=False
            )

        # Search all the cards with a reserve cost smaller than or equal to 4
        value = 4
        filter = f"?query={quote('rc<=')}{value}"
        with self.subTest(filter=filter):
            response = self.client.get(url + filter)
            query_cards = Card.objects.filter(stats__recall_cost__lte=value)
            self.assertQuerySetEqual(
                query_cards, response.context["card_list"], ordered=False
            )

    def test_card_list_x_advanced_filters(self):
        """Test the view of all the Cards after applying a filter on the query to find
        the Cards with a specific word in its effects.
        """
        value = "findme"
        character = Card.objects.filter(type=Card.Type.CHARACTER).first()
        spell = Card.objects.filter(type=Card.Type.SPELL).first()
        character.main_effect = value
        character.save()
        spell.echo_effect = value
        spell.save()

        response = self.client.get(reverse("cards") + f"?query=x:{value}")

        query_cards = Card.objects.filter(
            Q(main_effect__icontains=value) | Q(echo_effect__icontains=value)
        )
        self.assertQuerySetEqual(
            query_cards, response.context["card_list"], ordered=False
        )

    def test_card_list_st_advanced_filters(self):
        """Test the view of all the Cards after applying a filter on the query to find
        the Cards with a subtype with a specific word in its name.
        """

        value = "findme"
        subtype = Subtype.objects.create(reference=value, name=value)
        character = Card.objects.filter(type=Card.Type.CHARACTER).first()
        spell = Card.objects.filter(type=Card.Type.SPELL).first()
        character.subtypes.add(subtype)
        spell.subtypes.add(subtype)

        response = self.client.get(reverse("cards") + f"?query=st:{value}")
        query_cards = Card.objects.filter(
            Exists(Subtype.objects.filter(card=OuterRef("pk"), name__icontains=value))
        )
        self.assertQuerySetEqual(
            query_cards, response.context["card_list"], ordered=False
        )

    def test_card_list_t_advanced_filters(self):
        """Test the view of all the Cards after applying a filter on the query to find
        the Cards with specific triggers.
        """

        character = Card.objects.filter(type=Card.Type.CHARACTER).first()
        character.main_effect = "{J} I trigger when played"
        character.save()
        permanent = Card.objects.filter(type=Card.Type.LANDMARK_PERMANENT).first()
        permanent.main_effect = "{H} I trigger from hand {T} You can exhaust me"
        permanent.save()
        spell = Card.objects.filter(type=Card.Type.SPELL).first()
        spell.main_effect = "{R} I trigger from reserve"
        spell.echo_effect = "{D} You can discard me"
        spell.save()

        url = reverse("cards")

        # Search for Cards that trigger when they enter the battlefield
        filter = "?query=t:etb"
        with self.subTest(filter=filter):
            response = self.client.get(url + filter)
            query_cards = Card.objects.filter(main_effect__contains="{J}")
            self.assertQuerySetEqual(
                query_cards, response.context["card_list"], ordered=False
            )

        # Search for Cards that trigger when they are cast form the hand
        filter = "?query=t:hand"
        with self.subTest(filter=filter):
            response = self.client.get(url + filter)
            query_cards = Card.objects.filter(main_effect__contains="{H}")
            self.assertQuerySetEqual(
                query_cards, response.context["card_list"], ordered=False
            )

        # Search for Cards that trigger when they are cast from the reserve
        filter = "?query=t:reserve"
        with self.subTest(filter=filter):
            response = self.client.get(url + filter)
            query_cards = Card.objects.filter(main_effect__contains="{R}")
            self.assertQuerySetEqual(
                query_cards, response.context["card_list"], ordered=False
            )

        # Search for Cards that trigger by discarding them from the reserve
        filter = "?query=t:discard"
        with self.subTest(filter=filter):
            response = self.client.get(url + filter)
            query_cards = Card.objects.filter(echo_effect__contains="{D}")
            self.assertQuerySetEqual(
                query_cards, response.context["card_list"], ordered=False
            )

        # Search for Cards that trigger when they get exhausted
        filter = "?query=t:exhaust"
        with self.subTest(filter=filter):
            response = self.client.get(url + filter)
            query_cards = Card.objects.filter(main_effect__contains="{T}")
            self.assertQuerySetEqual(
                query_cards, response.context["card_list"], ordered=False
            )

        # Search for a trigger than doesn't exist
        filter = "?query=t:dontexist"
        with self.subTest(filter=filter):
            response = self.client.get(url + filter)
            query_cards = Card.objects.all()
            self.assertQuerySetEqual(
                query_cards, response.context["card_list"], ordered=False
            )


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
        url = self.pl.get_absolute_url()
        response = self.client.get(url)

        self.assertRedirects(
            response, get_login_url(next=url), status_code=HTTPStatus.FOUND
        )

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
        with silence_logging():
            response = self.client.get(url)

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
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
        with silence_logging():
            response = self.client.get(url)

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, "errors/404.html")

    def test_authenticated_by_another_user(self):
        """Test the view of a Deck through a PrivateLink when requested by an
        authenticated user other than the owner.
        """
        self.client.force_login(self.other_user)
        response = self.client.get(self.pl.get_absolute_url())

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed("decks/deck_detail.html")

    def test_authenticated_by_owner(self):
        """Test the view of a Deck through a PrivateLink when requested by the owner."""
        self.client.force_login(self.user)
        response = self.client.get(self.pl.get_absolute_url())

        self.assertRedirects(
            response, self.pl_deck.get_absolute_url(), status_code=HTTPStatus.FOUND
        )

    def test_authenticated_to_public_deck(self):
        """Test the view of a public Deck through a PrivateLink."""
        public_deck = Deck.objects.filter(owner=self.other_user, is_public=True).first()
        pl = PrivateLink.objects.create(deck=public_deck)

        self.client.force_login(self.user)
        response = self.client.get(pl.get_absolute_url())

        self.assertRedirects(
            response, public_deck.get_absolute_url(), status_code=HTTPStatus.FOUND
        )


class CreatePrivateLinkViewTestCase(BaseViewTestCase, AjaxTestCase):
    """Test case focusing on the view that creates a PrivateLink for a Deck."""

    def test_ajax_request(self):
        deck = Deck.objects.get(owner=self.user, name=self.PRIVATE_DECK_NAME)
        test_url = reverse("create-private-link", kwargs={"pk": deck.id})
        self.assert_ajax_protocol(test_url, self.user)

    def test_unauthenticated(self):
        """Test the view to add a Card to a Deck with an unauthenticated user."""
        deck = Deck.objects.get(owner=self.user, name=self.PRIVATE_DECK_NAME)
        test_url = reverse("create-private-link", kwargs={"pk": deck.id})
        headers = {
            "HTTP_X_REQUESTED_WITH": "XMLHttpRequest",
            "content_type": "application/json",
        }

        response = self.client.post(test_url, **headers)
        self.assertRedirects(
            response, get_login_url(next=test_url), status_code=HTTPStatus.FOUND
        )

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
        self.client.force_login(self.user)

        # Test a request targeting a nonexistent deck id
        wrong_url = reverse("create-private-link", kwargs={"pk": 100_000})
        with silence_logging():
            response = self.client.post(wrong_url, **headers)
        self.assert_ajax_error(response, HTTPStatus.NOT_FOUND, "Deck not found")

        # Test a request with valid data
        response = self.client.post(test_url, **headers)

        pl = PrivateLink.objects.get(deck=deck)
        response_data = response.json()["data"]
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(response_data["created"])
        self.assertEqual(response_data["link"], pl.get_absolute_url())

        # Test a request with valid data, which will not create the link
        response = self.client.post(test_url, **headers)

        pl.refresh_from_db()
        response_data = response.json()["data"]
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertFalse(response_data["created"])
        self.assertEqual(response_data["link"], pl.get_absolute_url())
        self.assertEqual(PrivateLink.objects.filter(deck=deck).count(), 1)

        # Test a request with valid data and a public deck
        public_deck = Deck.objects.filter(owner=self.user, is_public=True).first()
        wrong_url = reverse("create-private-link", kwargs={"pk": public_deck.id})
        with silence_logging():
            response = self.client.post(wrong_url, **headers)

        self.assert_ajax_error(response, HTTPStatus.BAD_REQUEST, "Invalid request")
        self.assertFalse(PrivateLink.objects.filter(deck=public_deck).exists())

        # Test a request with valid data and a not-owned deck
        not_owned_deck = Deck.objects.filter(
            owner=self.other_user, is_public=False
        ).first()
        wrong_url = reverse("create-private-link", kwargs={"pk": not_owned_deck.id})
        with silence_logging():
            response = self.client.post(wrong_url, **headers)

        self.assert_ajax_error(response, HTTPStatus.NOT_FOUND, "Deck not found")
        self.assertFalse(PrivateLink.objects.filter(deck=not_owned_deck).exists())
