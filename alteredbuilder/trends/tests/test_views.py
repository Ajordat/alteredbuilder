from http import HTTPStatus

from django.test import TestCase
from django.urls import reverse

from decks.models import Card
from decks.tests.utils import generate_card


class TrendsViewTestCase(TestCase):

    def test_home_unauthenticated(self):
        """Test case that validates the trends view renders correctly for
        unauthenticated users.

        Ensures that the current version's template is retrieved successfully.
        """
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, HTTPStatus.OK)
        # TODO: Assert faction_trends
        # TODO: Assert hero_trends
        # TODO: Assert card_trends

    def test_trends_filters(self):
        """Test case that validates the results of the trends when filtering by faction
        or hero.
        """

        test_faction = Card.Faction.MUNA
        response = self.client.get(reverse("home") + f"?faction={test_faction}")

        self.assertDictEqual(response.context["faction_trends"], {test_faction: 1})
        # TODO: Assert hero_trends
        # TODO: Assert card_trends

        test_hero = generate_card(Card.Faction.BRAVOS, Card.Type.HERO, card_set="CORE")

        response = self.client.get(
            reverse("home") + f"?hero={test_hero.name.split(" ")[0]}"
        )

        # self.assertDictEqual(response.context["faction_trends"], {test_hero.faction: 1})
        # self.assertDictEqual(
        #     response.context["hero_trends"],
        #     {test_hero.name: {"count": 1, "faction": test_hero.faction}},
        # )
        # TODO: Assert card_trends
