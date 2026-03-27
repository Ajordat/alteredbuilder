import json
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Exists, F, OuterRef
from django.db.models.query import QuerySet
from django.views.generic.list import ListView

from decks.deck_utils import (
    filter_by_faction,
    filter_by_legality,
    filter_by_other,
    filter_by_tags,
    filter_by_query,
)
from decks.models import CardInDeck, Deck, LovePoint, Tag
from profiles.models import Follow


class DeckListView(ListView):
    """ListView to display the public decks.
    If the user is authenticated, their decks are added to the context.
    """

    model = Deck
    queryset = (
        Deck.objects.filter(is_public=True)
        .select_related("owner", "hero")
        .prefetch_related("tags")
    )
    paginate_by = 32

    def get_queryset(self) -> QuerySet[Deck]:
        """Return a queryset with the Decks that match the filters in the GET params.

        Returns:
            QuerySet[Deck]: The decks to list.
        """
        qs = super().get_queryset()

        # Retrieve the query and search by deck name, hero name or owner
        query = self.request.GET.get("query")
        qs, self.query_tags = filter_by_query(qs, query)

        # Extract the faction filter
        factions = self.request.GET.get("faction")
        qs = filter_by_faction(qs, factions)

        # Extract the legality filter
        legality = self.request.GET.get("legality")
        qs = filter_by_legality(qs, legality)

        # Extract the tags filter
        tags = self.request.GET.get("tag")
        qs = filter_by_tags(qs, tags)

        # Extract the other filters
        other_filters = self.request.GET.get("other")
        qs = filter_by_other(qs, other_filters, self.request.user)

        if self.request.user.is_authenticated:
            qs = qs.annotate(
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

        order = self.request.GET.get("order")
        match (order):
            case "love":
                qs = qs.order_by("-love_count", "-modified_at")
            case "views":
                qs = qs.order_by(
                    F("hit_count_generic__hits").desc(nulls_last=True), "-modified_at"
                )
            case _:
                qs = qs.order_by("-modified_at")

        # In the deck list view there's no need for these fields, which might be
        # expensive to fill into the model
        return qs.defer(
            "description",
            "cards",
            "standard_legality_errors",
            "draft_legality_errors",
        ).prefetch_related("hit_count_generic")

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """If the user is authenticated, add their loved decks to the context.

        It also returns the checked filters so that they appear checked on the HTML.

        Returns:
            dict[str, Any]: The view's context.
        """
        context = super().get_context_data(**kwargs)

        # Extract the filters applied from the GET params and add them to the context
        # to fill them into the template
        checked_filters = []
        for filter in ["faction", "legality", "tag", "other"]:
            if filter in self.request.GET:
                checked_filters += self.request.GET[filter].split(",")
        context["checked_filters"] = checked_filters

        if "order" in self.request.GET:
            context["order"] = self.request.GET["order"]

        if "query" in self.request.GET:
            context["query"] = self.request.GET.get("query")
            context["query_tags"] = self.query_tags

        context["tags"] = Tag.objects.order_by("-type", "pk").values_list(
            "name", flat=True
        )

        # Build a mapping of deck ID -> list of {reference, quantity} for collection
        # availability checking on the frontend
        deck_ids = [
            deck.pk for deck in context["deck_list"] if deck.is_standard_legal
        ]
        cards_in_decks = (
            CardInDeck.objects.filter(deck_id__in=deck_ids)
            .select_related("card")
            .values_list("deck_id", "card__reference", "quantity")
        )
        deck_cards = {}
        for deck_id, reference, quantity in cards_in_decks:
            deck_cards.setdefault(deck_id, []).append(
                {"ref": reference, "qty": quantity}
            )
        # Pre-serialize per-deck card data for embedding on each deck element
        context["deck_cards_map"] = {
            deck_id: json.dumps(cards) for deck_id, cards in deck_cards.items()
        }

        return context


class OwnDeckListView(LoginRequiredMixin, DeckListView):
    """ListView to display the own decks."""

    model = Deck
    queryset = Deck.objects.select_related("owner", "hero").prefetch_related("tags")
    paginate_by = 24
    template_name = "decks/own_deck_list.html"

    def get_queryset(self) -> QuerySet[Deck]:
        """Return a queryset with the Decks created by the user.

        Returns:
            QuerySet[Deck]: Decks created by the user.
        """
        qs = super().get_queryset()

        return qs.filter(owner=self.request.user)
