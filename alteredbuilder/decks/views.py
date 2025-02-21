from http import HTTPStatus
from typing import Any
import json
import os

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count, Exists, F, OuterRef, Q
from django.db.models.manager import Manager
from django.db.models.query import QuerySet
from django.http import Http404, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic.edit import FormView
from django.views.generic.list import ListView
from hitcount.views import HitCountDetailView

from api.utils import ajax_request, ApiJsonResponse
from decks.deck_utils import (
    create_new_deck,
    get_deck_details,
    filter_by_faction,
    filter_by_legality,
    filter_by_other,
    filter_by_tags,
    import_unique_card,
    parse_card_query_syntax,
    filter_by_query,
    patch_deck,
    remove_card_from_deck,
)
from decks.game_modes import update_deck_legality
from decks.models import (
    Card,
    CardInDeck,
    Comment,
    CommentVote,
    Deck,
    FavoriteCard,
    LovePoint,
    PrivateLink,
    Set,
    Tag,
)
from decks.forms import (
    CardImportForm,
    CommentForm,
    DecklistForm,
    DeckMetadataForm,
    DeckTagsForm,
)
from decks.exceptions import AlteredAPIError, CardAlreadyExists, MalformedDeckException
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
    paginate_by = 30

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


class DeckDetailView(HitCountDetailView):
    """DetailView to display the detail of a Deck model."""

    model = Deck
    count_hit = True

    def get_queryset(self) -> Manager[Deck]:
        """When retrieving the object, we need to make sure that the Deck is public or
        the User is its owner.

        Returns:
            Manager[Deck]: The view's queryset.
        """
        qs = super().get_queryset()
        filter = Q(is_public=True)
        if self.request.user.is_authenticated:
            filter |= Q(owner=self.request.user)
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
        # I don't fancy making these queries here. Maybe I could store that information
        # on the UserProfile model
        qs = qs.annotate(
            follower_count=Count("owner__followers", distinct=True),
            following_count=Count("owner__following", distinct=True),
        )
        return (
            qs.filter(filter)
            .select_related("hero", "owner", "owner__profile")
            .prefetch_related("tags")
        )

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """Add metadata of the Deck to the context.

        Returns:
            dict[str, Any]: The view's context.
        """

        context = super().get_context_data(**kwargs)
        context |= get_deck_details(self.object)
        context["metadata_form"] = DeckMetadataForm(
            initial={
                "name": self.object.name,
                "description": self.object.description,
                "is_public": self.object.is_public,
            }
        )
        context["tags_form"] = DeckTagsForm(
            initial={"tags": list(self.object.tags.values_list("pk", flat=True))}
        )
        context["comment_form"] = CommentForm()
        comments_qs = Comment.objects.filter(deck=self.object).select_related(
            "user", "user__profile"
        )
        if self.request.user.is_authenticated:
            comments_qs = comments_qs.annotate(
                is_upvoted=Exists(
                    CommentVote.objects.filter(
                        comment=OuterRef("pk"), user=self.request.user
                    )
                )
            )
        context["comments"] = comments_qs
        return context


class PrivateLinkDeckDetailView(LoginRequiredMixin, DeckDetailView):
    """DetailView to display the detail of a Deck model by using a private link."""

    def get(self, request, *args, **kwargs):
        self.object: Deck = self.get_object()
        if self.object.owner == request.user or self.object.is_public:
            # If the owner is accessing with the private link or the Deck is public,
            # redirect to the official one
            return redirect(self.object.get_absolute_url())
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_queryset(self) -> Manager[Deck]:
        """When retrieving the object, we need to make sure that the code matches with
        the requested Deck.

        Returns:
            Manager[Deck]: The view's queryset.
        """
        code = self.kwargs["code"]
        deck_id = self.kwargs["pk"]
        try:
            link = PrivateLink.objects.get(code=code, deck__id=deck_id)
            link.last_accessed_at = timezone.now()
            link.save(update_fields=["last_accessed_at"])
            return (
                Deck.objects.filter(id=deck_id)
                .select_related("hero", "owner", "owner__profile")
                .annotate(
                    follower_count=Count("owner__followers", distinct=True),
                    following_count=Count("owner__following", distinct=True),
                )
            )
        except PrivateLink.DoesNotExist:
            raise Http404("Private link does not exist")


class NewDeckFormView(LoginRequiredMixin, FormView):
    """FormView to manage the creation of a Deck.
    It requires being authenticated.
    """

    template_name = "decks/new_deck.html"
    form_class = DecklistForm

    def get_initial(self) -> dict[str, Any]:
        """Function to modify the initial values of the form.

        Returns:
            dict[str, Any]: Initial values
        """
        initial = super().get_initial()
        if "decklist" in self.request.GET:
            initial["decklist"] = self.request.GET["decklist"]
        elif "hero" in self.request.GET:
            initial["decklist"] = f"1 {self.request.GET['hero']}"

        return initial

    def form_valid(self, form: DecklistForm) -> HttpResponse:
        """Function called once a submitted DecklistForm has been validated.
        Convert the submitted input into a Deck object. If there's any errors on the
        input, render it to the user.

        Args:
            form (DecklistForm): The submitted information.

        Returns:
            HttpResponse: The view's response.
        """
        # Create deck
        try:
            self.deck = create_new_deck(self.request.user, form.cleaned_data)

        except MalformedDeckException as e:
            # If the deck contains any error, render it to the user
            form.add_error("decklist", e.detail)
            return self.form_invalid(form)

        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Return the redirect URL for a successful Deck submission.
        Redirect to the Deck's detail view.

        Returns:
            str: The Deck's detail endpoint.
        """
        return self.deck.get_absolute_url()


@login_required
def delete_deck(request: HttpRequest, pk: int) -> HttpResponse:
    """View to delete a Deck.

    Args:
        request (HttpRequest): The request.
        pk (int): The ID of the Deck to be deleted.

    Returns:
        HttpResponse: The response.
    """

    # The user is part of the filter to ensure ownership.
    # The delete statement won't fail even if the filter doesn't match any record, which
    # means that if the Deck is not found (doesn't exist or isn't owned) the view will
    # fail silently and redirect the user to their Decks regardless of the result.
    Deck.objects.filter(pk=pk, owner=request.user).delete()
    return redirect("own-deck")


@login_required
def love_deck(request: HttpRequest, pk: int) -> HttpResponse:
    """View to add a LovePoint to a Deck. If the Deck is already loved by the user,
    it will be undone.

    Args:
        request (HttpRequest): The request.
        pk (int): The ID of the Deck to act upon.

    Raises:
        PermissionDenied: If the user does not have access to the Deck.

    Returns:
        HttpResponse: The response.
    """
    try:
        # The Deck must be either public or owned
        deck = Deck.objects.filter(Q(is_public=True) | Q(owner=request.user)).get(pk=pk)
        # Retrieve the LovePoint by the user to this Deck
        love_point = LovePoint.objects.get(deck=deck, user=request.user)
    except LovePoint.DoesNotExist:
        # If the LovePoint does not exist, create it and increase the `love_count`
        LovePoint.objects.create(deck=deck, user=request.user)
        deck.love_count = F("love_count") + 1
        deck.save(update_fields=["love_count"])
    except Deck.DoesNotExist:
        # If the Deck is not found (private and not owned), raise a permission error
        raise PermissionDenied
    else:
        # If the LovePoint exists, delete it and decrease the `love_count`
        with transaction.atomic():
            love_point.delete()
            deck.love_count = F("love_count") - 1
            deck.save(update_fields=["love_count"])
    return redirect(deck.get_absolute_url())


@login_required
@ajax_request()
def update_deck(request: HttpRequest, pk: int) -> HttpResponse:
    """Function to update a deck with AJAX.

    Args:
        request (HttpRequest): Received request
        pk (int): Id of the target deck

    Returns:
        HttpResponse: A JSON response indicating whether the request succeeded or not.
    """
    try:
        data = json.load(request)

        match data["action"]:
            case "add":
                # Not currently used
                # The deck is retrieved for validation purposes
                deck = Deck.objects.get(pk=pk, owner=request.user)
                status = {"added": False}
            case "delete":
                deck = Deck.objects.get(pk=pk, owner=request.user)
                remove_card_from_deck(deck, data["card_reference"])
                status = {"deleted": True}
            case "patch":
                if not data["name"]:
                    return ApiJsonResponse(
                        _("The deck must have a name"), HTTPStatus.UNPROCESSABLE_ENTITY
                    )
                if pk == 0:
                    deck = Deck.objects.create(
                        owner=request.user, name=data["name"], is_public=True
                    )
                else:
                    deck = Deck.objects.get(pk=pk, owner=request.user)
                patch_deck(deck, data["name"], data["decklist"])
                status = {"patched": True, "deck": deck.id}
            case _:
                raise KeyError("Invalid action")

        update_deck_legality(deck)
        deck.save()
    except Deck.DoesNotExist:
        return ApiJsonResponse(_("Deck not found"), HTTPStatus.NOT_FOUND)
    except (Card.DoesNotExist, CardInDeck.DoesNotExist):
        return ApiJsonResponse(_("Card not found"), HTTPStatus.NOT_FOUND)
    except KeyError:
        return ApiJsonResponse(_("Invalid payload"), HTTPStatus.BAD_REQUEST)
    return ApiJsonResponse(status, HTTPStatus.OK)


@login_required
@ajax_request()
def vote_comment(request: HttpRequest, pk: int, comment_pk: int) -> HttpResponse:
    """Function to upvote a Comment with AJAX.

    Args:
        request (HttpRequest): Received request
        pk (int): Id of the target deck
        comment_pk (int): Id of the target comment

    Returns:
        HttpResponse: A JSON response indicating whether the request succeeded or not.
    """
    try:
        comment = Comment.objects.get(pk=comment_pk, deck__pk=pk)
        comment_vote = CommentVote.objects.get(user=request.user, comment=comment)
        comment_vote.delete()
        comment.vote_count = F("vote_count") - 1
        comment.save()
        status = {"deleted": True}
    except CommentVote.DoesNotExist:
        CommentVote.objects.create(user=request.user, comment=comment)
        comment.vote_count = F("vote_count") + 1
        comment.save()
        status = {"created": True}
    except Comment.DoesNotExist:
        return ApiJsonResponse(_("Comment not found"), HTTPStatus.NOT_FOUND)

    return ApiJsonResponse(status, HTTPStatus.OK)


@login_required
@ajax_request()
def delete_comment(request: HttpRequest, pk: int, comment_pk: int) -> HttpResponse:
    """Function to delete a Comment with AJAX.

    Args:
        request (HttpRequest): Received request
        pk (int): Id of the target deck
        comment_pk (int): Id of the target comment

    Returns:
        HttpResponse: A JSON response indicating whether the request succeeded or not.
    """
    try:
        deck = Deck.objects.get(pk=pk)
        comment = Comment.objects.get(pk=comment_pk, deck=deck, user=request.user)
        comment.delete()
        deck.comment_count = F("comment_count") - 1
        deck.save(update_fields=["comment_count"])

        status = {"deleted": True}
    except Comment.DoesNotExist:
        return ApiJsonResponse(_("Comment not found"), HTTPStatus.NOT_FOUND)
    except Deck.DoesNotExist:
        return ApiJsonResponse(_("Deck not found"), HTTPStatus.NOT_FOUND)

    return ApiJsonResponse(status, HTTPStatus.OK)


@login_required
@ajax_request()
def create_private_link(request: HttpRequest, pk: int) -> HttpResponse:
    """Function to create a PrivateLink with AJAX.
    Ideally it should be moved to the API app.

    Args:
        request (HttpRequest): Received request
        pk (int): Id of the target deck

    Returns:
        HttpResponse: A JSON response indicating whether the request succeeded or not.
    """
    try:
        # Retrieve the referenced Deck
        deck = Deck.objects.get(pk=pk, owner=request.user)
        if deck.is_public:
            return JsonResponse(
                {
                    "error": {
                        "code": HTTPStatus.BAD_REQUEST,
                        "message": _("Invalid request"),
                    }
                },
                status=HTTPStatus.BAD_REQUEST,
            )

        pl, created = PrivateLink.objects.get_or_create(deck=deck)
        status = {"created": created, "link": pl.get_absolute_url()}

    except Deck.DoesNotExist:
        return JsonResponse(
            {"error": {"code": HTTPStatus.NOT_FOUND, "message": _("Deck not found")}},
            status=HTTPStatus.NOT_FOUND,
        )
    return JsonResponse({"data": status}, status=HTTPStatus.OK)


@login_required
def update_deck_metadata(request: HttpRequest, pk: int) -> HttpResponse:
    """
    View to update the metadata fields of a Deck.

    Args:
        request: The HTTP request object.
        pk: The primary key of the Deck to update.

    Returns:
        HttpResponse: The response object.
    """

    # Retrieve the Deck by ID
    deck = get_object_or_404(Deck, pk=pk)

    if deck.owner != request.user:
        # For some unknown reason, this is returning 405 instead of 403
        raise PermissionDenied

    if request.method == "POST":
        # Instantiate the form with the POST data
        form = DeckMetadataForm(request.POST)
        if form.is_valid():
            # Update the Deck's metadata fields with the form data
            deck.name = form.cleaned_data["name"]
            deck.description = form.cleaned_data["description"]
            deck.is_public = form.cleaned_data["is_public"]
            deck.save()

    return redirect(deck.get_absolute_url())


@login_required
def update_tags(request: HttpRequest, pk: int) -> HttpResponse:
    if request.method == "POST":
        form = DeckTagsForm(request.POST)
        if form.is_valid():
            try:
                deck = Deck.objects.get(pk=pk, owner=request.user)

                primary_tag = form.cleaned_data["primary_tags"]
                secondary_tags = form.cleaned_data["secondary_tags"]

                deck.tags.clear()
                if primary_tag:
                    deck.tags.add(primary_tag)
                deck.tags.add(*secondary_tags)

            except Deck.DoesNotExist:
                raise PermissionDenied

            return redirect(deck.get_absolute_url())
        else:
            # Weird, but should be logged
            pass

    return redirect(reverse("deck-detail", kwargs={"pk": pk}))


@login_required
def create_comment(request: HttpRequest, pk: int) -> HttpResponse:
    """
    View to create a Comment for a Deck.

    Args:
        request: The HTTP request object.
        pk: The primary key of the Deck for which a comment is being created.

    Returns:
        HttpResponse: The response object.
    """

    deck = get_object_or_404(Deck, pk=pk, is_public=True)

    if request.method == "POST":
        # Instantiate the form with the POST data
        form = CommentForm(request.POST)
        if form.is_valid():
            # Create a new comment linked to the deck and user
            Comment.objects.create(
                user=request.user, deck=deck, body=form.cleaned_data["body"]
            )

            # Increment the comment count on the Deck model
            deck.comment_count = F("comment_count") + 1
            deck.save(update_fields=["comment_count"])

    return redirect(deck.get_absolute_url())


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
                    context["edit_deck"] = Deck.objects.filter(
                        pk=edit_deck_id, owner=self.request.user
                    ).get()
                    edit_deck_cards = (
                        CardInDeck.objects.filter(deck=context["edit_deck"])
                        .select_related("card")
                        .order_by("card__reference")
                    )
                    characters = []
                    spells = []
                    permanents = []

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
                    context["character_cards"] = characters
                    context["spell_cards"] = spells
                    context["permanent_cards"] = permanents

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
        context["sets"] = Set.objects.all()
        context["other_filters"] = [
            ("Promo", _("Promo")),
            ("AltArt", _("Alternate Art")),
            ("Owned", _("In my collection")),
        ]

        return context


@login_required
def import_card(request: HttpRequest) -> HttpResponse:
    """Receive the reference of a unique card and import it into the database.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The response object.
    """
    context = {}
    form = None
    if request.method == "POST":
        form = CardImportForm(request.POST)
        if form.is_valid():
            reference = form.cleaned_data["reference"]
            try:
                # Attempt to import a unique card
                card = import_unique_card(reference)
                # Automatically favorite the card
                FavoriteCard.objects.create(user=request.user, card=card)

                # Fill the context
                context["message"] = _(
                    "The card '%(card_name)s' (%(reference)s) was successfully imported."
                ) % {"card_name": card.name, "reference": reference}
                form = None
                context["card"] = card
            except CardAlreadyExists:
                # If the card already exists, inform the user
                card = Card.objects.get(reference=reference)
                # Automatically favorite the card if it wasn't already
                FavoriteCard.objects.get_or_create(user=request.user, card=card)

                # Fill the context
                context["message"] = _(
                    "This unique version of '%(card_name)s' (%(reference)s) already exists in the database."
                ) % {"card_name": card.name, "reference": reference}
                form = None
                context["card"] = card
            except AlteredAPIError as e:
                # If the import operation fails, attempt to explain the failure
                if e.status_code == HTTPStatus.UNAUTHORIZED:
                    form.add_error(
                        "reference",
                        _("The card '%(reference)s' is not public")
                        % {"reference": reference},
                    )
                else:
                    form.add_error(
                        "reference", _("Failed to fetch the card on the official API.")
                    )

    context["form"] = (
        form
        if form
        else CardImportForm(initial={"reference": request.GET.get("reference")})
    )

    return render(request, "decks/import_card.html", context)


def deck_legality_view(request):
    json_path = os.path.join(os.path.dirname(__file__), "data", "legality.json")

    with open(json_path, "r", encoding="utf-8") as json_file:
        data = json.load(json_file)

    last_update_date = data.get("last_update", "Unknown date")
    patches = data.get("patches", [])

    return render(
        request,
        "decks/legality_changelog.html",
        {"last_update_date": last_update_date, "patches": patches},
    )
