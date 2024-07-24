from datetime import timedelta
from typing import Any

from django.db.models import Count, F, Q
from django.utils.timezone import localdate
from django.utils.translation import get_language, gettext_lazy as _
from django.views.generic.base import TemplateView

from hitcount.models import Hit
from decks.models import Card, CardInDeck, Deck, LovePoint
from .models import FactionTrend


class HomeView(TemplateView):
    template_name = "trends/home.html"
    TRENDING_COUNT = 10

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        today = localdate()

        try:
            faction = Card.Faction(self.request.GET.get("faction"))
        except ValueError:
            faction = None
        try:
            hero_name = self.request.GET.get("hero")
        except ValueError:
            hero_name = None

        # Retrieve loved decks
        if self.request.user.is_authenticated:
            context["loved_decks"] = (
                LovePoint.objects.filter(user=self.request.user)
                .with_faction(faction)
                .values_list("deck__id", flat=True)
            )

        # Retrieve the most hits made in the last 7 days and sort them DESC
        time_lapse = today - timedelta(days=7)
        trending_deck_pks = (
            Hit.objects.filter(created__date__gte=time_lapse)
            .values("hitcount")
            .alias(total=Count("hitcount"))
            .order_by("-total")[: self.TRENDING_COUNT]
            .values_list("hitcount__object_pk", flat=True)
        )
        # Add the most viewed decks to the context
        context["trending"] = (
            Deck.objects.filter(id__in=trending_deck_pks, is_public=True)
            .with_faction(faction)
            .with_hero(hero_name)
            .select_related("owner", "hero")
            .prefetch_related("hit_count_generic")
            .order_by("-hit_count_generic__hits")
        )

        faction_trends = FactionTrend.objects.filter(date=today).order_by("-count")
        if faction:
            faction_trends = faction_trends.filter(faction=faction)
        context["faction_trends"] = {t.faction: t.count for t in faction_trends}

        hero_trends = (
            Deck.objects.filter(
                modified_at__date__gte=time_lapse, is_public=True, hero__isnull=False
            )
            .with_faction(faction)
            .with_hero(hero_name)
            .annotate(hero_name=F(f"hero__name_{get_language()}"))
            .values("hero_name", "hero__faction")
            .annotate(count=Count("hero_name"))
            .order_by("-count")
        )
        context["hero_trends"] = {
            hero["hero_name"]: {
                "faction": hero["hero__faction"],
                "count": hero["count"],
            }
            for hero in hero_trends
        }

        card_trends = (
            CardInDeck.objects.filter(
                deck__modified_at__date__gte=time_lapse, deck__is_public=True
            )
            .with_faction(faction)
            .with_hero(hero_name)
            .annotate(name=F(f"card__name_{get_language()}"))
            .values("name", "card__faction")
            .alias(count=Count("name"))
            .order_by("-count")[:10]
        )
        context["card_trends"] = card_trends

        return context
