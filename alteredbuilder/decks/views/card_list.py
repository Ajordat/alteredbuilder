from typing import Any

from django.db.models import F, Q
from django.db.models.query import QuerySet
from django.utils.translation import gettext_lazy as _
from django.views.generic.list import ListView

from decks.deck_utils import parse_card_query_syntax
from decks.models import Card, CardInDeck, Deck, Set


class CardListView(ListView):
    """View to list and filter all the Cards."""

    model = Card
    paginate_by = 24

    def get_queryset(self) -> QuerySet[Card]:
        """Return a queryset matching the filters received via GET parameters.

        Returns:
            QuerySet[Card]: The list of Cards.
        """
        qs = super().get_queryset()
        filters = Q()
        self.filter_sets = None

        # Retrieve the text query and search by name
        query = self.request.GET.get("query")
        if query:
            qs, query_tags, has_reference = parse_card_query_syntax(qs, query)
            self.query_tags = query_tags
            if has_reference:
                return qs
        else:
            self.query_tags = None

        # Retrieve the Faction filters.
        # If any value is invalid, this filter will not be applied.
        factions = self.request.GET.get("faction")
        if factions:
            try:
                factions = [Card.Faction(faction) for faction in factions.split(",")]
            except ValueError:
                pass
            else:
                filters &= Q(faction__in=factions)

        # Retrieve the Other filters.
        other_filters = self.request.GET.get("other")
        if other_filters:
            filters &= Q(
                is_promo="Promo" in other_filters, is_alt_art="AltArt" in other_filters
            )
            retrieve_owned = "Owned" in other_filters
        else:
            filters &= Q(is_promo=False, is_alt_art=False)
            retrieve_owned = False

        # Retrieve the Rarity filters.
        # If any value is invalid, this filter will not be applied.
        rarities = self.request.GET.get("rarity")
        if rarities:
            try:
                rarities = [Card.Rarity(rarity) for rarity in rarities.split(",")]
            except ValueError:
                pass
            else:
                if Card.Rarity.UNIQUE in rarities and retrieve_owned:
                    rarities.remove(Card.Rarity.UNIQUE)
                    if self.request.user.is_authenticated:
                        filters &= Q(rarity__in=rarities) | (
                            Q(rarity=Card.Rarity.UNIQUE)
                            & Q(favorited_by__user=self.request.user)
                        )
                    else:
                        filters &= Q(rarity__in=rarities)
                else:
                    filters &= Q(rarity__in=rarities)
        else:
            filters &= ~Q(rarity=Card.Rarity.UNIQUE)

        # Retrieve the Type filters.
        # If any value is invalid, this filter will not be applied.
        card_types = self.request.GET.get("type")
        if card_types:
            try:
                card_types = [
                    Card.Type(card_type) for card_type in card_types.split(",")
                ]
            except ValueError:
                pass
            else:
                filters &= Q(type__in=card_types)

        # Retrieve the Set filters.
        # If any value is invalid, this filter will not be applied.
        card_sets = self.request.GET.get("set")
        if card_sets:
            self.filter_sets = Set.objects.filter(code__in=card_sets.split(","))
            filters &= Q(set__in=self.filter_sets)

        query_order = []
        order_param = self.request.GET.get("order")
        if order_param:
            # Subtract the "-" simbol pointing that the order will be inversed
            if desc := "-" in order_param:
                clean_order_param = order_param[1:]
            else:
                clean_order_param = order_param

            if clean_order_param in ["name", "rarity"]:
                query_order = [order_param]

            elif clean_order_param in ["mana", "reserve"]:
                # Due to the unique 1-to-1 relationship of the Card types, it is needed
                # to use Coalesce to try and order by different fields
                if clean_order_param == "mana":
                    fields = "stats__main_cost"
                else:
                    fields = "stats__recall_cost"

                mana_order = F(fields)
                if desc:
                    mana_order = mana_order.desc()
                query_order = [mana_order]

                qs = qs.exclude(type=Card.Type.HERO)
            # If the order is inversed, the "reference" used as the second clause of
            # ordering also needs to be reversed
            query_order += ["-reference" if desc else "reference"]
        else:
            query_order = ["reference"]

        return qs.filter(filters).order_by(*query_order)

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """Add extra context to the view.

        If the user is authenticated, include the Decks owned to fill the modal to add
        a Card to a Deck.

        The filters applied are also returned to display their values on the template.

        Returns:
            dict[str, Any]: The template's context.
        """
        context = super().get_context_data(**kwargs)

        context["all_cards"] = {}
        if self.request.user.is_authenticated:
            # If the user is authenticated, add the list of decks owned to be displayed
            # on the sidebar
            context["own_decks"] = (
                Deck.objects.filter(owner=self.request.user)
                .order_by("-modified_at")
                .values("id", "name", "hero__faction")
            )
            edit_deck_id = self.request.GET.get("deck")
            if edit_deck_id:
                # If a Deck is currently being edited, add its data to the context
                try:
                    deck = Deck.objects.filter(
                        pk=edit_deck_id, owner=self.request.user
                    ).get()
                    context["edit_deck"] = deck
                    edit_deck_cards = (
                        CardInDeck.objects.filter(deck=deck)
                        .select_related("card")
                        .order_by("card__reference")
                    )
                    characters = []
                    spells = []
                    permanents = []
                    all_cards = {deck.hero.reference: 1} if deck.hero else {}

                    for cid in edit_deck_cards:
                        match cid.card.type:
                            case Card.Type.CHARACTER:
                                characters.append(cid)
                            case Card.Type.SPELL:
                                spells.append(cid)
                            case (
                                Card.Type.LANDMARK_PERMANENT
                                | Card.Type.EXPEDITION_PERMANENT
                            ):
                                permanents.append(cid)
                        all_cards[cid.card.reference] = cid.quantity
                    context["character_cards"] = characters
                    context["spell_cards"] = spells
                    context["permanent_cards"] = permanents
                    context["all_cards"] = all_cards

                except Deck.DoesNotExist:
                    pass

        # Retrieve the selected filters and structure them so that they can be marked
        # as checked
        checked_filters = []
        for filter in ["faction", "rarity", "type", "set", "other"]:
            if filter in self.request.GET:
                checked_filters += self.request.GET[filter].split(",")
        context["checked_filters"] = checked_filters
        context["checked_sets"] = self.filter_sets
        if "order" in self.request.GET:
            context["order"] = self.request.GET["order"]
        if "query" in self.request.GET:
            context["query"] = self.request.GET.get("query")
            context["query_tags"] = self.query_tags

        # Add all sets to the context
        context["sets"] = Set.objects.filter(is_main_set=True)
        context["other_filters"] = [
            ("Promo", _("Promo")),
            ("AltArt", _("Alternate Art")),
            ("Owned", _("In my collection")),
        ]

        return context
