from datetime import timedelta
from typing import Any

from django.core.management.base import BaseCommand, CommandParser
from django.db.models import Count, F, OuterRef, Q, Subquery
from django.utils.timezone import localdate
from hitcount.models import Hit

from decks.models import Card, CardInDeck, Deck, Set
from trends.models import CardTrend, DeckTrend, FactionTrend, HeroTrend


DEFAULT_TIME_LAPSE = 7
CARD_RANKING_LIMIT = 10
DECK_RANKING_LIMIT = 10


class Command(BaseCommand):
    help = "Generates statistics for the past X (default=7) days"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--days",
            action="store",
            default=DEFAULT_TIME_LAPSE,
            type=int,
            dest="day_count",
        )

    def handle(self, *args: Any, **options: Any) -> str | None:

        self.day_count = options["day_count"]
        self.yesterday = localdate() - timedelta(days=1)

        self.time_lapse = self.yesterday - timedelta(days=self.day_count)

        self.generate_faction_trends()
        self.generate_hero_trends()
        self.generate_card_trends()
        self.generate_deck_trends()

    def generate_faction_trends(self):
        faction_trends = (
            Deck.objects.filter(
                Q(is_standard_legal=True) | Q(is_exalts_legal=True),
                modified_at__date__gte=self.time_lapse,
                is_public=True,
            )
            .values("hero__faction")
            .annotate(count=Count("hero__faction"))
            .order_by("-count")
        )
        for record in faction_trends:
            FactionTrend.objects.update_or_create(
                faction=record["hero__faction"],
                count=record["count"],
                day_count=self.day_count,
                date=self.yesterday,
            )

    def generate_hero_trends(self):
        hero_trends = (
            Deck.objects.filter(
                Q(is_standard_legal=True) | Q(is_exalts_legal=True),
                modified_at__date__gte=self.time_lapse,
                is_public=True,
            )
            .annotate(hero_name=F("hero__name_en"))
            .values("hero_name")
            .annotate(count=Count("hero_name"))
            .order_by("-count")
        )

        core_set = Set.objects.get(code="CORE")
        for record in hero_trends:
            hero = Card.objects.get(
                type=Card.Type.HERO, name=record["hero_name"], set=core_set
            )

            HeroTrend.objects.update_or_create(
                hero=hero,
                count=record["count"],
                day_count=self.day_count,
                date=self.yesterday,
            )

    def generate_card_trends(self):

        legality_filter = [
            Q(deck__is_standard_legal=True) | Q(deck__is_exalts_legal=True)
        ]
        base_filter = {
            "deck__modified_at__date__gte": self.time_lapse,
            "deck__is_public": True,
        }

        card_trends = (
            CardInDeck.objects.filter(*legality_filter, **base_filter)
            .annotate(name=F("card__name_en"))
            .values("name", "card__faction", "card__rarity")
            .alias(count=Count("name"))
            .order_by("-count")[:CARD_RANKING_LIMIT]
        )
        core_set = Set.objects.get(code="CORE")
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
                ranking=rank,
                day_count=self.day_count,
                date=self.yesterday,
            )

        trending_factions = FactionTrend.objects.filter(
            date=self.yesterday
        ).values_list("faction", flat=True)
        for faction in trending_factions:
            card_trends = (
                CardInDeck.objects.filter(*legality_filter, **base_filter)
                .filter(card__faction=faction)
                .annotate(name=F("card__name_en"))
                .values("name", "card__faction", "card__rarity")
                .alias(count=Count("name"))
                .order_by("-count")[:CARD_RANKING_LIMIT]
            )
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
                    ranking=rank,
                    day_count=self.day_count,
                    date=self.yesterday,
                )

        trending_heroes = HeroTrend.objects.filter(date=self.yesterday)
        for hero_trend in trending_heroes:
            card_trends = (
                CardInDeck.objects.filter(*legality_filter, **base_filter)
                .filter(deck__hero__name_en=hero_trend.hero.name)
                .annotate(name=F("card__name_en"))
                .values("name", "card__faction", "card__rarity")
                .alias(count=Count("name"))
                .order_by("-count")[:CARD_RANKING_LIMIT]
            )

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
                    ranking=rank,
                    day_count=self.day_count,
                    date=self.yesterday,
                )

    def generate_deck_trends(self):

        legality_filter = [Q(is_standard_legal=True) | Q(is_exalts_legal=True)]
        base_filter = {
            "is_public": True,
        }

        deck_trends = (
            Deck.objects.filter(*legality_filter, **base_filter)
            .alias(
                recent_hits=Subquery(
                    Hit.objects.filter(
                        created__date__gte=self.time_lapse,
                        hitcount__object_pk=OuterRef("pk"),
                    )
                    .values("hitcount__object_pk")
                    .annotate(count=Count("pk"))
                    .values("count")
                )
            )
            .order_by(F("recent_hits").desc(nulls_last=True))[:DECK_RANKING_LIMIT]
        )

        for rank, record in enumerate(deck_trends, start=1):
            DeckTrend.objects.update_or_create(
                deck=record,
                hero=None,
                faction=None,
                ranking=rank,
                day_count=self.day_count,
                date=self.yesterday,
            )

        trending_factions = FactionTrend.objects.filter(
            date=self.yesterday
        ).values_list("faction", flat=True)

        for faction in trending_factions:
            deck_trends = (
                Deck.objects.filter(*legality_filter, **base_filter)
                .filter(hero__faction=faction)
                .alias(
                    recent_hits=Subquery(
                        Hit.objects.filter(
                            created__date__gte=self.time_lapse,
                            hitcount__object_pk=OuterRef("pk"),
                        )
                        .values("hitcount__object_pk")
                        .annotate(count=Count("pk"))
                        .values("count")
                    )
                )
                .order_by(F("recent_hits").desc(nulls_last=True))[:DECK_RANKING_LIMIT]
            )
            for rank, record in enumerate(deck_trends, start=1):
                DeckTrend.objects.update_or_create(
                    deck=record,
                    hero=None,
                    faction=faction,
                    ranking=rank,
                    day_count=self.day_count,
                    date=self.yesterday,
                )

        trending_heroes = HeroTrend.objects.filter(date=self.yesterday)

        for hero_trend in trending_heroes:
            deck_trends = (
                Deck.objects.filter(*legality_filter, **base_filter)
                .filter(hero__name_en=hero_trend.hero.name)
                .alias(
                    recent_hits=Subquery(
                        Hit.objects.filter(
                            created__date__gte=self.time_lapse,
                            hitcount__object_pk=OuterRef("pk"),
                        )
                        .values("hitcount__object_pk")
                        .annotate(count=Count("pk"))
                        .values("count")
                    )
                )
                .order_by(F("recent_hits").desc(nulls_last=True))[:DECK_RANKING_LIMIT]
            )
            for rank, record in enumerate(deck_trends, start=1):
                DeckTrend.objects.update_or_create(
                    deck=record,
                    hero=hero_trend.hero,
                    faction=None,
                    ranking=rank,
                    day_count=self.day_count,
                    date=self.yesterday,
                )
