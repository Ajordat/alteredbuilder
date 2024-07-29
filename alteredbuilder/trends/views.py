from datetime import timedelta
from typing import Any

from django.db.models import Count, Exists, F, OuterRef, Q, Subquery
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

        # Retrieve the most hits made in the last 7 days and sort them DESC
        time_lapse = yesterday - timedelta(days=7)
        # Add the most viewed decks to the context
        trending_decks = Deck.objects.filter(is_public=True).filter(
            Q(is_standard_legal=True) | Q(is_exalts_legal=True)
        )

        if faction:
            trending_decks = trending_decks.filter(hero__faction=faction)
        if hero:
            trending_decks = trending_decks.filter(hero__name__startswith=hero_name)

        trending_decks = (
            trending_decks.annotate(
                recent_hits=Subquery(
                    Hit.objects.filter(
                        created__date__gte=time_lapse,
                        hitcount__object_pk=OuterRef("pk"),
                    )
                    .values("hitcount__object_pk")
                    .annotate(count=Count("pk"))
                    .values("count")
                )
            )
            .select_related("owner", "hero")
            .prefetch_related("hit_count_generic")
            .order_by(F("recent_hits").desc(nulls_last=True))[: self.TRENDING_COUNT]
        )

        if self.request.user.is_authenticated:
            trending_decks = trending_decks.annotate(
                is_loved=Exists(
                    LovePoint.objects.filter(
                        deck=OuterRef("pk"), user=self.request.user
                    )
                )
            )
        context["trending"] = trending_decks

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
        hero_trends = (
            HeroTrend.objects.filter(date=yesterday)
            .order_by("-count")
            .select_related("hero")
        )
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

        card_trends = (
            CardTrend.objects.filter(date=yesterday)
            .select_related("card")
            .order_by("ranking")
        )
        if hero:
            filters = Q(hero=hero)
        elif faction:
            filters = Q(faction=faction)
        else:
            filters = Q(faction__isnull=True) & Q(hero__isnull=True)

        card_trends = card_trends.filter(filters).annotate(
            prev_ranking=CardTrend.objects.filter(
                card=OuterRef("card_id"), date=yesterday - timedelta(days=1)
            )
            .filter(filters)
            .values("ranking")
        )

        context["card_trends"] = card_trends

        return context
