from django.test import TestCase
from django.utils.timezone import localdate

from decks.tests.utils import generate_card
from decks.models import Card
from trends.models import CardTrend


class TrendsModelsTestCase(TestCase):
    """Test case focusing on the Models."""

    @classmethod
    def setUpTestData(cls):
        """Create the database data for this test.

        Specifically, it creates:
        * 1 Character
        * 1 CardTrend
        """
        card = generate_card(Card.Faction.AXIOM, Card.Type.CHARACTER)
        CardTrend.objects.create(card=card, date=localdate())

    def test_to_string(self):
        """Test the string representations of all models."""
        card_trend = CardTrend.objects.first()

        self.assertEqual(
            str(card_trend),
            f"{card_trend.ranking} - {card_trend.card} [{card_trend.faction}] [{card_trend.hero}]",
        )
