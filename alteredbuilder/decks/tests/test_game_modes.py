from django.contrib.auth.models import User
from django.test import TestCase

from decks.game_modes import GameMode, update_deck_legality
from decks.models import Card, CardInDeck, Deck
from .utils import generate_card


class GameModesTestCase(TestCase):
    """Test case focusing on the game modes."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="test_user")

    def test_deck_total_count(self):
        hero = generate_card(Card.Faction.AXIOM, Card.Type.HERO, Card.Rarity.COMMON)
        deck = Deck.objects.create(owner=self.user, name="deck_name", hero=hero)

        update_deck_legality(deck)

        self.assertFalse(deck.is_standard_legal)
        self.assertIn(
            GameMode.ErrorCode.ERR_NOT_ENOUGH_CARD_COUNT, deck.standard_legality_errors
        )
        self.assertFalse(deck.is_draft_legal)
        self.assertIn(
            GameMode.ErrorCode.ERR_NOT_ENOUGH_CARD_COUNT, deck.draft_legality_errors
        )

        CardInDeck.objects.create(
            deck=deck,
            quantity=3,
            card=generate_card(
                Card.Faction.AXIOM, Card.Type.CHARACTER, Card.Rarity.RARE
            ),
        )
        CardInDeck.objects.create(
            deck=deck,
            quantity=3,
            card=generate_card(
                Card.Faction.AXIOM, Card.Type.CHARACTER, Card.Rarity.RARE
            ),
        )
        CardInDeck.objects.create(
            deck=deck,
            quantity=3,
            card=generate_card(
                Card.Faction.AXIOM, Card.Type.CHARACTER, Card.Rarity.RARE
            ),
        )
        CardInDeck.objects.create(
            deck=deck,
            quantity=3,
            card=generate_card(
                Card.Faction.AXIOM, Card.Type.CHARACTER, Card.Rarity.RARE
            ),
        )
        CardInDeck.objects.create(
            deck=deck,
            quantity=3,
            card=generate_card(
                Card.Faction.AXIOM, Card.Type.CHARACTER, Card.Rarity.RARE
            ),
        )
        CardInDeck.objects.create(
            deck=deck,
            quantity=3,
            card=generate_card(
                Card.Faction.AXIOM, Card.Type.CHARACTER, Card.Rarity.UNIQUE
            ),
        )
        CardInDeck.objects.create(
            deck=deck,
            quantity=3,
            card=generate_card(
                Card.Faction.AXIOM, Card.Type.CHARACTER, Card.Rarity.COMMON
            ),
        )
        CardInDeck.objects.create(
            deck=deck,
            quantity=3,
            card=generate_card(
                Card.Faction.AXIOM, Card.Type.CHARACTER, Card.Rarity.COMMON
            ),
        )
        CardInDeck.objects.create(
            deck=deck,
            quantity=3,
            card=generate_card(
                Card.Faction.AXIOM, Card.Type.CHARACTER, Card.Rarity.COMMON
            ),
        )
        CardInDeck.objects.create(
            deck=deck,
            quantity=3,
            card=generate_card(
                Card.Faction.AXIOM, Card.Type.CHARACTER, Card.Rarity.COMMON
            ),
        )

        update_deck_legality(deck)

        self.assertFalse(deck.is_standard_legal)
        self.assertIn(
            GameMode.ErrorCode.ERR_NOT_ENOUGH_CARD_COUNT, deck.standard_legality_errors
        )
        self.assertTrue(deck.is_draft_legal)
        self.assertListEqual(deck.draft_legality_errors, [])

        CardInDeck.objects.create(
            deck=deck,
            quantity=3,
            card=generate_card(
                Card.Faction.AXIOM, Card.Type.CHARACTER, Card.Rarity.COMMON
            ),
        )
        CardInDeck.objects.create(
            deck=deck,
            quantity=3,
            card=generate_card(
                Card.Faction.AXIOM, Card.Type.CHARACTER, Card.Rarity.COMMON
            ),
        )
        CardInDeck.objects.create(
            deck=deck,
            quantity=3,
            card=generate_card(
                Card.Faction.AXIOM, Card.Type.CHARACTER, Card.Rarity.COMMON
            ),
        )

        update_deck_legality(deck)

        self.assertTrue(deck.is_standard_legal)
        self.assertListEqual(deck.standard_legality_errors, [])
        self.assertTrue(deck.is_draft_legal)
        self.assertListEqual(deck.draft_legality_errors, [])

    def test_deck_faction_count(self):
        hero = generate_card(Card.Faction.AXIOM, Card.Type.HERO, Card.Rarity.COMMON)
        deck = Deck.objects.create(owner=self.user, name="deck_name", hero=hero)
        CardInDeck.objects.create(
            deck=deck,
            quantity=3,
            card=generate_card(
                Card.Faction.LYRA, Card.Type.CHARACTER, Card.Rarity.COMMON
            ),
        )

        update_deck_legality(deck)

        self.assertFalse(deck.is_standard_legal)
        self.assertIn(
            GameMode.ErrorCode.ERR_EXCEED_FACTION_COUNT, deck.standard_legality_errors
        )
        self.assertFalse(deck.is_draft_legal)
        self.assertNotIn(
            GameMode.ErrorCode.ERR_EXCEED_FACTION_COUNT, deck.draft_legality_errors
        )
        self.assertIn(
            GameMode.ErrorCode.ERR_NOT_ENOUGH_CARD_COUNT, deck.draft_legality_errors
        )

        CardInDeck.objects.create(
            deck=deck,
            quantity=3,
            card=generate_card(
                Card.Faction.ORDIS, Card.Type.CHARACTER, Card.Rarity.COMMON
            ),
        )
        CardInDeck.objects.create(
            deck=deck,
            quantity=3,
            card=generate_card(
                Card.Faction.MUNA, Card.Type.CHARACTER, Card.Rarity.COMMON
            ),
        )

        update_deck_legality(deck)

        self.assertFalse(deck.is_draft_legal)
        self.assertIn(
            GameMode.ErrorCode.ERR_EXCEED_FACTION_COUNT, deck.draft_legality_errors
        )

    def test_deck_rare_count(self):
        hero = generate_card(Card.Faction.AXIOM, Card.Type.HERO, Card.Rarity.COMMON)
        deck = Deck.objects.create(owner=self.user, name="deck_name", hero=hero)
        CardInDeck.objects.create(
            deck=deck,
            quantity=3,
            card=generate_card(
                Card.Faction.AXIOM, Card.Type.CHARACTER, Card.Rarity.RARE
            ),
        )
        CardInDeck.objects.create(
            deck=deck,
            quantity=3,
            card=generate_card(
                Card.Faction.AXIOM, Card.Type.CHARACTER, Card.Rarity.RARE
            ),
        )
        CardInDeck.objects.create(
            deck=deck,
            quantity=3,
            card=generate_card(
                Card.Faction.AXIOM, Card.Type.CHARACTER, Card.Rarity.RARE
            ),
        )
        CardInDeck.objects.create(
            deck=deck,
            quantity=3,
            card=generate_card(
                Card.Faction.AXIOM, Card.Type.CHARACTER, Card.Rarity.RARE
            ),
        )
        CardInDeck.objects.create(
            deck=deck,
            quantity=3,
            card=generate_card(
                Card.Faction.AXIOM, Card.Type.CHARACTER, Card.Rarity.RARE
            ),
        )
        CardInDeck.objects.create(
            deck=deck,
            quantity=3,
            card=generate_card(
                Card.Faction.AXIOM, Card.Type.CHARACTER, Card.Rarity.RARE
            ),
        )

        update_deck_legality(deck)

        self.assertFalse(deck.is_standard_legal)
        self.assertIn(
            GameMode.ErrorCode.ERR_EXCEED_RARE_COUNT, deck.standard_legality_errors
        )
        self.assertFalse(deck.is_draft_legal)
        self.assertNotIn(
            GameMode.ErrorCode.ERR_EXCEED_RARE_COUNT, deck.draft_legality_errors
        )

    def test_deck_unique_count(self):
        hero = generate_card(Card.Faction.AXIOM, Card.Type.HERO, Card.Rarity.COMMON)
        deck = Deck.objects.create(owner=self.user, name="deck_name", hero=hero)
        CardInDeck.objects.create(
            deck=deck,
            quantity=3,
            card=generate_card(
                Card.Faction.AXIOM, Card.Type.CHARACTER, Card.Rarity.UNIQUE
            ),
        )
        CardInDeck.objects.create(
            deck=deck,
            quantity=3,
            card=generate_card(
                Card.Faction.AXIOM, Card.Type.CHARACTER, Card.Rarity.UNIQUE
            ),
        )

        update_deck_legality(deck)

        self.assertFalse(deck.is_standard_legal)
        self.assertIn(
            GameMode.ErrorCode.ERR_EXCEED_UNIQUE_COUNT, deck.standard_legality_errors
        )
        self.assertFalse(deck.is_draft_legal)
        self.assertNotIn(
            GameMode.ErrorCode.ERR_EXCEED_UNIQUE_COUNT, deck.draft_legality_errors
        )
