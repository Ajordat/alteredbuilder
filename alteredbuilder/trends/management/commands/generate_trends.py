from datetime import timedelta
from typing import Any

from django.core.management.base import BaseCommand, CommandParser
from django.db.models import Count, F, Q
from django.utils.timezone import localdate

from decks.models import Card, CardInDeck, Deck, Set
from trends.models import FactionTrend, HeroTrend, CardTrend


DEFAULT_TIME_LAPSE = 7
CARD_RANKING_LIMIT = 10


class Command(BaseCommand):
    """This command looks at the modified Decks within the last X days to generate some
    statistics to generate some trends. The information is stored in the *Trend tables.

    The analyzed timelapse always ends on the previous day and starts on the previous X
    days.
    """

    help = "Generates statistics for the past X (default=7) days"

    def add_arguments(self, parser: CommandParser) -> None:
        """Add the `days` argument to the CLI to modify the amount of days the trends
        look back to to generate the trends.

        Args:
            parser (CommandParser): The CLI parser.
        """
        parser.add_argument(
            "--days",
            action="store",
            default=DEFAULT_TIME_LAPSE,
            type=int,
            dest="day_count",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Entrypoint of the command. Generate the timelapse that will be analyzed and
        start the trend generation.
        """

        # Calculate the time lapse
        self.day_count = options["day_count"]
        self.end_lapse = localdate() - timedelta(days=1)
        self.start_lapse = self.end_lapse - timedelta(days=self.day_count)

        # Generate the trends
        self.generate_faction_trends()
        self.generate_hero_trends()
        self.generate_card_trends()

    def generate_faction_trends(self):
        """Generate the faction trends."""

        # Extract the faction trends
        faction_trends = (
            Deck.objects.filter(
                Q(is_standard_legal=True) | Q(is_exalts_legal=True),
                modified_at__date__gte=self.start_lapse,
                is_public=True,
            )
            .values("hero__faction")
            .annotate(count=Count("hero__faction"))
            .order_by("-count")
        )
        # Generate a trend record for each faction
        for record in faction_trends:
            FactionTrend.objects.update_or_create(
                faction=record["hero__faction"],
                day_count=self.day_count,
                date=self.end_lapse,
                defaults={"count": record["count"]},
            )

    def generate_hero_trends(self):
        """Generate the hero trends."""

        # Extract the hero cards used in each legal public deck and sort them DESC
        # To get the card the name is used instead of the reference. This is done to
        # take into consideration the same hero in the different sets, such as the
        # promotional cards and the Kickstarter
        hero_trends = (
            Deck.objects.filter(
                Q(is_standard_legal=True) | Q(is_exalts_legal=True),
                modified_at__date__gte=self.start_lapse,
                is_public=True,
            )
            .annotate(hero_name=F("hero__name_en"))
            .values("hero_name")
            .annotate(count=Count("hero_name"))
            .order_by("-count")
        )

        # Use the core set version of the card
        core_set = Set.objects.get(code="CORE")
        # Create a HeroTrend record for each hero
        for record in hero_trends:
            hero = Card.objects.get(
                type=Card.Type.HERO, name=record["hero_name"], set=core_set
            )

            HeroTrend.objects.update_or_create(
                hero=hero,
                day_count=self.day_count,
                date=self.end_lapse,
                defaults={"count": record["count"]},
            )

    def generate_card_trends(self):
        """Generate the card trends. There will be 10 records for:
        * General (once)
        * Each faction (6 factions)
        * Each hero (18 heroes)
        Therefore 250 records are generated each time.

        A card's popularity is extracted from their inclusion in the decks modified
        within the time lapse. The quantity is ignored, therefore having 3 or 1 copies
        of a card in a Deck have the same weight.

        The Card's name and rarity are used to identify a Card instead of its reference
        to count the usage of the same card from a different set.
        """

        # Base filters that will be used recurrently when retrieving the cards
        legality_filter = [
            Q(deck__is_standard_legal=True) | Q(deck__is_exalts_legal=True)
        ]
        base_filter = {
            "deck__modified_at__date__gte": self.start_lapse,
            "deck__is_public": True,
        }

        # This is the general usage, therefore no filtering based on faction or hero is
        # applied
        card_trends = (
            CardInDeck.objects.filter(*legality_filter, **base_filter)
            .annotate(name=F("card__name_en"))
            .values("name", "card__faction", "card__rarity")
            .alias(count=Count("name"))
            .order_by("-count")[:CARD_RANKING_LIMIT]
        )
        # Get the card from the core set
        core_set = Set.objects.get(code="CORE")

        # Create a record for each card
        for rank, record in enumerate(card_trends, start=1):
            card = Card.objects.get(
                name=record["name"],
                rarity=record["card__rarity"],
                faction=record["card__faction"],
                set=core_set,
            )
            CardTrend.objects.update_or_create(
                card=card,
                hero=None,
                faction=None,
                day_count=self.day_count,
                date=self.end_lapse,
                defaults={"ranking": rank},
            )

        # Iterate the trending factions (all) and create a ranking for each
        trending_factions = FactionTrend.objects.filter(
            date=self.end_lapse
        ).values_list("faction", flat=True)
        for faction in trending_factions:

            # Extract the card usage filtering by faction
            card_trends = (
                CardInDeck.objects.filter(*legality_filter, **base_filter)
                .filter(card__faction=faction)
                .annotate(name=F("card__name_en"))
                .values("name", "card__faction", "card__rarity")
                .alias(count=Count("name"))
                .order_by("-count")[:CARD_RANKING_LIMIT]
            )

            # Create a record for each card
            for rank, record in enumerate(card_trends, start=1):
                card = Card.objects.get(
                    name=record["name"],
                    rarity=record["card__rarity"],
                    faction=record["card__faction"],
                    set=core_set,
                )
                CardTrend.objects.update_or_create(
                    card=card,
                    hero=None,
                    faction=faction,
                    day_count=self.day_count,
                    date=self.end_lapse,
                    defaults={"ranking": rank},
                )

        # Iterate the trending heroes (all) and create a ranking for each
        trending_heroes = HeroTrend.objects.filter(date=self.end_lapse)
        for hero_trend in trending_heroes:

            # Extract the card usage filtering by the hero name
            card_trends = (
                CardInDeck.objects.filter(*legality_filter, **base_filter)
                .filter(deck__hero__name_en=hero_trend.hero.name)
                .annotate(name=F("card__name_en"))
                .values("name", "card__faction", "card__rarity")
                .alias(count=Count("name"))
                .order_by("-count")[:CARD_RANKING_LIMIT]
            )

            # Create a record for each card
            for rank, record in enumerate(card_trends, start=1):
                card = Card.objects.get(
                    name=record["name"],
                    rarity=record["card__rarity"],
                    faction=record["card__faction"],
                    set=core_set,
                )
                CardTrend.objects.update_or_create(
                    card=card,
                    hero=hero_trend.hero,
                    faction=None,
                    day_count=self.day_count,
                    date=self.end_lapse,
                    defaults={"ranking": rank},
                )
