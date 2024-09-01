from datetime import timedelta
from typing import Any

from django.db.models import Exists, OuterRef, Q
from django.utils.timezone import localdate
from django.views.generic.base import TemplateView

from decks.models import Card, Deck, LovePoint
from profiles.models import Follow
from trends.models import CardTrend, FactionTrend, HeroTrend


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
            hero = Card.objects.filter(
                type=Card.Type.HERO, name__startswith=hero_name, set__code="CORE"
            ).first()
        except (ValueError, Card.DoesNotExist):
            hero = None

        # Retrieve the trending decks
        deck_trends = (
            Deck.objects.filter(is_public=True)
            .filter(Q(is_standard_legal=True) | Q(is_exalts_legal=True))
            .filter(
                Q(trend__date=yesterday)
                & Q(trend__hero=hero)
                & Q(trend__faction=faction)
            )
            .select_related("owner", "hero")
            .prefetch_related("hit_count_generic")
        )

        if self.request.user.is_authenticated:
            deck_trends = deck_trends.annotate(
                is_loved=Exists(
                    LovePoint.objects.filter(
                        deck=OuterRef("pk"), user=self.request.user
                    )
                ),
                is_followed=Exists(
                    Follow.objects.filter(
                        followed=OuterRef("owner"), follower=self.request.user
                    )
                ),
            )

        context["deck_trends"] = deck_trends.order_by("trend__ranking")

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

        card_trends = card_trends.filter(Q(hero=hero) & Q(faction=faction)).annotate(
            prev_ranking=CardTrend.objects.filter(
                card=OuterRef("card_id"), date=yesterday - timedelta(days=1)
            ).filter(Q(hero=hero) & Q(faction=faction)).values("ranking")
        )

        context["card_trends"] = card_trends

        return context
