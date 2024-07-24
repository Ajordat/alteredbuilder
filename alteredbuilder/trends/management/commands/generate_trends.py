from datetime import timedelta
from typing import Any

from django.core.management.base import BaseCommand, CommandParser
from django.db.models import Count, F
from django.utils.timezone import localdate

from decks.models import Deck, Hero, Set
from trends.models import FactionTrend, HeroTrend


class Command(BaseCommand):
    help = "Generates statistics for the past X (default=7) days"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--days", action="store", default=7, type=int, dest="day_count"
        )

    def handle(self, *args: Any, **options: Any) -> str | None:

        self.day_count = options["day_count"]
        self.today = localdate()

        self.time_lapse = self.today - timedelta(days=self.day_count)

        self.generate_faction_trends()
        self.generate_hero_trends()

    def generate_faction_trends(self):
        faction_trends = (
            Deck.objects.filter(
                modified_at__date__gte=self.time_lapse,
                is_public=True,
                hero__isnull=False,
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
                date=self.today,
            )

    def generate_hero_trends(self):
        hero_trends = (
            Deck.objects.filter(
                modified_at__date__gte=self.time_lapse,
                is_public=True,
                hero__isnull=False,
            )
            .annotate(hero_name=F(f"hero__name_en"))
            .values("hero_name")
            .annotate(count=Count("hero_name"))
            .order_by("-count")
        )

        core_set = Set.objects.get(code="CORE")
        for record in hero_trends:
            hero = Hero.objects.get(name=record["hero_name"], set=core_set)

            HeroTrend.objects.update_or_create(
                hero=hero,
                count=record["count"],
                day_count=self.day_count,
                date=self.today,
            )
