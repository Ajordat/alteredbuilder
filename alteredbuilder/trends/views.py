from datetime import timedelta
from typing import Any

from django.db.models import Count
from django.utils.timezone import localdate
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import TemplateView

from hitcount.models import Hit
from decks.models import Card, Deck, Hero, LovePoint
from .models import CardTrend, FactionTrend, HeroTrend


class HomeView(TemplateView):
    template_name = "trends/home.html"
    TRENDING_COUNT = 10

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        yesterday = localdate() - timedelta(days=1)

        try:
            faction = Card.Faction(self.request.GET.get("faction"))
        except ValueError:
            faction = None

        try:
            hero_name = self.request.GET.get("hero")
            hero = Hero.objects.filter(
                name__startswith=hero_name, set__code="CORE"
            ).first()
        except (ValueError, Hero.DoesNotExist):
            hero = None

        # Retrieve loved decks
        if self.request.user.is_authenticated:
            context["loved_decks"] = (
                LovePoint.objects.filter(user=self.request.user)
                .with_faction(faction)
                .values_list("deck__id", flat=True)
            )

        # Retrieve the most hits made in the last 7 days and sort them DESC
        time_lapse = yesterday - timedelta(days=7)
        trending_deck_pks = (
            Hit.objects.filter(created__date__gte=time_lapse)
            .values("hitcount")
            .alias(total=Count("hitcount"))
            .order_by("-total")
            .values_list("hitcount__object_pk", flat=True)
        )
        # Add the most viewed decks to the context
        context["trending"] = (
            Deck.objects.filter(id__in=trending_deck_pks, is_public=True)
            .with_faction(faction)
            .with_hero(hero_name)
            .select_related("owner", "hero")
            .prefetch_related("hit_count_generic")
            .order_by("-hit_count_generic__hits")[: self.TRENDING_COUNT]
        )

        if hero:
            faction_trends = {hero.faction: 1}
        elif faction:
            faction_trends = {faction: 1}
        else:
            faction_trends = FactionTrend.objects.filter(date=yesterday).order_by(
                "-count"
            )
            faction_trends = {t.faction: t.count for t in faction_trends}

        context["faction_trends"] = faction_trends

        # Retrieve hero trends
        hero_trends = HeroTrend.objects.filter(date=yesterday).order_by("-count")
        if hero:
            hero_trends = {hero.name: {"faction": hero.faction, "count": 1}}
        else:
            if faction:
                hero_trends = hero_trends.filter(hero__faction=faction)
            hero_trends = {
                t.hero.name: {"faction": t.hero.faction, "count": t.count}
                for t in hero_trends
            }
        context["hero_trends"] = hero_trends

        card_trends = CardTrend.objects.filter(date=yesterday).order_by("-ranking")
        if hero:
            card_trends = card_trends.filter(hero=hero)
        elif faction:
            card_trends = card_trends.filter(faction=faction)
        else:
            card_trends = card_trends.filter(faction__isnull=True, hero__isnull=True)
        context["card_trends"] = card_trends

        return context
