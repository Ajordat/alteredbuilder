from datetime import timedelta
from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import CommandParser
from django.db.models import Count, F, IntegerField, OuterRef, Q, Subquery, Sum
from django.utils.timezone import localdate
from hitcount.models import Hit

from config.commands import BaseCommand
from decks.models import Card, CardInDeck, Deck, Set
from trends.models import CardTrend, DeckTrend, FactionTrend, HeroTrend, UserTrend


DEFAULT_TIME_LAPSE = 7
CARD_RANKING_LIMIT = 10
DECK_RANKING_LIMIT = 10
USER_RANKING_LIMIT = 10


class Command(BaseCommand):
    """This command looks at the modified Decks within the last X days to generate some
    statistics to generate some trends. The information is stored in the *Trend tables.

    The analyzed timelapse always ends on the previous day and starts on the previous X
    days.
    """

    help = "Generates statistics for the past X (default=7) days"
    version = "1.0.0"

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
        self.generate_deck_trends()
        self.generate_user_trends()

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

        # Create a HeroTrend record for each hero
        for record in hero_trends:
            hero = Card.objects.filter(
                type=Card.Type.HERO,
                name=record["hero_name"],
                set__is_main_set=True,
                is_promo=False,
                is_alt_art=False,
            ).order_by("set__release_date").first()

            HeroTrend.objects.update_or_create(
                hero=hero,
                day_count=self.day_count,
                date=self.end_lapse,
                defaults={"count": record["count"]},
            )

    def generate_card_trends(self):
        """Generate the card trends.

        There will be 10 records for:
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
            "card__rarity__in": [Card.Rarity.COMMON, Card.Rarity.RARE],
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
        # Exclude the cards from the KS set
        ks_set = Set.objects.get(code="COREKS")

        # Create a record for each card
        for rank, record in enumerate(card_trends, start=1):
            card = Card.objects.exclude(set=ks_set).get(
                name=record["name"],
                rarity=record["card__rarity"],
                faction=record["card__faction"],
                is_promo=False,
                is_alt_art=False,
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
                card = Card.objects.exclude(set=ks_set).get(
                    name=record["name"],
                    rarity=record["card__rarity"],
                    faction=record["card__faction"],
                    is_promo=False,
                    is_alt_art=False,
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
                card = (
                    Card.objects.exclude(set=ks_set)
                    .filter(
                        name=record["name"],
                        rarity=record["card__rarity"],
                        faction=record["card__faction"],
                        is_alt_art=False,
                    )
                    .order_by("is_promo")[0]
                )
                CardTrend.objects.update_or_create(
                    card=card,
                    hero=hero_trend.hero,
                    faction=None,
                    day_count=self.day_count,
                    date=self.end_lapse,
                    defaults={"ranking": rank},
                )

    def generate_deck_trends(self):
        """Generate the deck trends.

        There will be 10 records for:
        * General (once)
        * Each faction (6 factions)
        * Each hero (18 heroes)
        Therefore 250 records are generated each time.

        A deck's popularity is extracted from their hit count within the time lapse.
        The total hitcount is ignored, it only matters the views in the time lapse.

        When generating the records for the heroes, the Card's name is used to identify
        a Card instead of its reference to take into consideration the usage of the
        same card from a different set.
        """

        # Base filters that will be used recurrently when retrieving the decks
        legality_filter = [Q(is_standard_legal=True) | Q(is_exalts_legal=True)]
        base_filter = {
            "is_public": True,
        }

        # Extract the sorted list of Decks based on the hits created in the time lapse
        deck_trends = (
            Deck.objects.filter(*legality_filter, **base_filter)
            .alias(
                recent_hits=Subquery(
                    Hit.objects.filter(
                        created__date__gte=self.start_lapse,
                        hitcount__object_pk=OuterRef("pk"),
                    )
                    .values("hitcount__object_pk")
                    .annotate(count=Count("pk"))
                    .values("count")
                )
            )
            .order_by(F("recent_hits").desc(nulls_last=True))[:DECK_RANKING_LIMIT]
        )

        # Create a record for each of the trending decks
        for rank, record in enumerate(deck_trends, start=1):
            DeckTrend.objects.update_or_create(
                deck=record,
                hero=None,
                faction=None,
                day_count=self.day_count,
                date=self.end_lapse,
                defaults={"ranking": rank},
            )

        # Iterate the trending factions (all)
        trending_factions = FactionTrend.objects.filter(
            date=self.end_lapse
        ).values_list("faction", flat=True)

        for faction in trending_factions:
            # Extract the decks but filter by faction
            deck_trends = (
                Deck.objects.filter(*legality_filter, **base_filter)
                .filter(hero__faction=faction)
                .alias(
                    recent_hits=Subquery(
                        Hit.objects.filter(
                            created__date__gte=self.start_lapse,
                            hitcount__object_pk=OuterRef("pk"),
                        )
                        .values("hitcount__object_pk")
                        .annotate(count=Count("pk"))
                        .values("count")
                    )
                )
                .order_by(F("recent_hits").desc(nulls_last=True))[:DECK_RANKING_LIMIT]
            )

            # Create a record for each trending deck of the faction
            for rank, record in enumerate(deck_trends, start=1):
                DeckTrend.objects.update_or_create(
                    deck=record,
                    hero=None,
                    faction=faction,
                    day_count=self.day_count,
                    date=self.end_lapse,
                    defaults={"ranking": rank},
                )

        # Iterate the trending heroes (all)
        trending_heroes = HeroTrend.objects.filter(date=self.end_lapse)

        for hero_trend in trending_heroes:
            # The name of the hero is used instead of its reference
            deck_trends = (
                Deck.objects.filter(*legality_filter, **base_filter)
                .filter(hero__name_en=hero_trend.hero.name)
                .alias(
                    recent_hits=Subquery(
                        Hit.objects.filter(
                            created__date__gte=self.start_lapse,
                            hitcount__object_pk=OuterRef("pk"),
                        )
                        .values("hitcount__object_pk")
                        .annotate(count=Count("pk"))
                        .values("count")
                    )
                )
                .order_by(F("recent_hits").desc(nulls_last=True))[:DECK_RANKING_LIMIT]
            )
            # Create a record for each trending deck of the hero
            for rank, record in enumerate(deck_trends, start=1):
                DeckTrend.objects.update_or_create(
                    deck=record,
                    hero=hero_trend.hero,
                    faction=None,
                    day_count=self.day_count,
                    date=self.end_lapse,
                    defaults={"ranking": rank},
                )

    def generate_user_trends(self):

        latest_hits = (
            Hit.objects.filter(
                created__date__gte=self.start_lapse,
                hitcount__object_pk=OuterRef("pk"),
            )
            .values("hitcount__object_pk")
            .annotate(hit_count=Count("pk"))
            .values("hit_count")
        )
        user_hits = (
            Deck.objects.filter(is_public=True)
            .annotate(recent_hits=Subquery(latest_hits, output_field=IntegerField()))
            .values("owner")
            .annotate(recent_hits=Sum("recent_hits"))
            .order_by(F("recent_hits").desc(nulls_last=True))[:USER_RANKING_LIMIT]
        )

        for record in user_hits:
            UserTrend.objects.update_or_create(
                user=get_user_model().objects.get(pk=record.get("owner")),
                day_count=self.day_count,
                date=self.end_lapse,
                defaults={"count": record.get("recent_hits", 0)},
            )
