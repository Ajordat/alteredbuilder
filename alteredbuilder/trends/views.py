from datetime import timedelta
from typing import Any, Optional

from django.db.models import Exists, OuterRef, Q
from django.db.models.query import QuerySet
from django.utils.timezone import localdate
from django.views.generic.base import TemplateView

from decks.models import Card, Deck, LovePoint
from profiles.models import Follow
from trends.models import CardTrend, FactionTrend, HeroTrend


class HomeView(TemplateView):
    """View to display the trending factions, heroes, cards and decks."""

    template_name = "trends/home.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Add the trends data to the context.

        Returns:
            dict[str, Any]: The view's context.
        """
        context = super().get_context_data(**kwargs)

        # Select the previous day
        self.current_date = localdate() - timedelta(days=1)
        try:
            # Convert the selected faction to the Card.Faction Enum
            faction = Card.Faction(self.request.GET.get("faction"))
        except ValueError:
            faction = None

        try:
            # Convert the selected hero to the Card in the CORE set
            hero_name = self.request.GET.get("hero")
            hero = (
                Card.objects.filter(type=Card.Type.HERO, name__startswith=hero_name)
                .filter(Q(set__code="CORE") | Q(set__code="CYCLONE"))
                .first()
            )
        except (ValueError, Card.DoesNotExist):
            hero = None

        # Extract the trends data
        context["faction_trends"] = self.extract_faction_trends(faction, hero)
        context["hero_trends"] = self.extract_hero_trends(faction, hero)
        context["card_trends"] = self.extract_card_trends(faction, hero)
        context["deck_trends"] = self.extract_deck_trends(faction, hero)

        return context

    def extract_faction_trends(
        self, faction: Optional[Card.Faction], hero: Optional[Card]
    ) -> dict[str, int]:
        """Extract the faction trends based on the filters received.

        The actual trends are only necessary when there are no filters selected. That's
        because the trends are based on percentage, hence if there's only one faction,
        that faction will be 1; or if it's a hero, it will be that hero's faction.

        Args:
            faction (Card.Faction | None): Filter by faction.
            hero (Card | None): Filter by hero.

        Returns:
            dict[str: int]: A dict with each faction and its proportion.
        """

        if hero:
            # Return the hero's faction
            faction_trends = {hero.faction: 1}
        elif faction:
            # Return the faction itself
            faction_trends = {faction: 1}
        else:
            # Extract the actual trend and build the dictionary
            faction_trends = FactionTrend.objects.filter(
                date=self.current_date
            ).order_by("-count")
            faction_trends = {t.faction: t.count for t in faction_trends}

        return faction_trends

    def extract_hero_trends(
        self, faction: Card.Faction | None, hero: Card | None
    ) -> dict[str, dict[str, Any]]:  # noqa: E203
        """Extract the hero trends based on the filters received.

        The actual trends are only necessary when not filtering by hero. That's because
        in that case, that hero's proportion will always be 1.

        Args:
            faction (Card.Faction | None): Filter by faction.
            hero (Card | None): Filter by hero.

        Returns:
            dict[str : dict[str, Any]]: A dict with each hero that contains its faction
                                        and its proportion.
        """

        if hero:
            # Return the hero itself
            hero_trends = {hero.name: {"faction": hero.faction, "count": 1}}
        else:
            # Extract the actual trend and build the dictionary
            hero_trends = (
                HeroTrend.objects.filter(date=self.current_date)
                .order_by("-count")
                .select_related("hero")
            )
            if faction:
                # If filtering by faction, apply the filter on the query
                hero_trends = hero_trends.filter(hero__faction=faction)

            hero_trends = {
                t.hero.name: {"faction": t.hero.faction, "count": t.count}
                for t in hero_trends
            }

        return hero_trends

    def extract_card_trends(
        self, faction: Card.Faction | None, hero: Card | None
    ) -> QuerySet[CardTrend]:
        """Extract the card trends based on the filters received.

        It adds a `prev_ranking` field to compare the growth or decrease in popularity
        against the previous ranking.

        Args:
            faction (Card.Faction | None): Filter by faction.
            hero (Card | None): Filter by hero.

        Returns:
            QuerySet[CardTrend]: A queryset containing the filtered trending cards.
        """

        return (
            CardTrend.objects.filter(date=self.current_date)
            .select_related("card")
            .order_by("ranking")
            .filter(Q(hero=hero) & Q(faction=faction))
            .annotate(
                prev_ranking=CardTrend.objects.filter(
                    card=OuterRef("card_id"), date=self.current_date - timedelta(days=1)
                )
                .filter(Q(hero=hero) & Q(faction=faction))
                .values("ranking")
            )
        )

    def extract_deck_trends(
        self, faction: Card.Faction | None, hero: Card | None
    ) -> QuerySet[Deck]:
        """Extract the deck trends based on the filters received.

        Args:
            faction (Card.Faction | None): Filter by faction.
            hero (Card | None): Filter by hero.

        Returns:
            QuerySet[CardTrend]: A queryset containing the filtered trending decks.
        """

        # Retrieve the trending decks
        deck_trends = (
            Deck.objects.filter(is_public=True)
            .filter(Q(is_standard_legal=True) | Q(is_nuc_legal=True))
            .filter(
                Q(trend__date=self.current_date)
                & Q(trend__hero=hero)
                & Q(trend__faction=faction)
            )
            .select_related("owner", "hero")
            .prefetch_related("hit_count_generic")
        )

        # If the user is authenticated, include whether the user likes any of the decks
        # or follows the creator
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

        return deck_trends.order_by("trend__ranking")
