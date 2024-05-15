from typing import Any
import json

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.db.models.manager import Manager
from django.db.models.query import QuerySet
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic.detail import DetailView
from django.views.generic.edit import FormView
from django.views.generic.list import ListView

from .deck_utils import create_new_deck, get_deck_details
from .game_modes import update_deck_legality
from .models import Card, CardInDeck, Deck
from .forms import DecklistForm, DeckMetadataForm, UpdateDeckForm
from .exceptions import MalformedDeckException


# Views for this app


class DeckListView(ListView):
    """ListView to display the public decks.
    If the user is authenticated, their decks are added to the context.
    """

    model = Deck
    queryset = (
        Deck.objects.filter(is_public=True)
        .select_related("owner", "hero")
        .order_by("-modified_at")
    )
    paginate_by = 24

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """If the user is authenticated, add their decks to the context.

        Returns:
            dict[str, Any]: The view's context.
        """
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context["own_decks"] = (
                Deck.objects.filter(owner=self.request.user)
                .select_related("hero")
                .order_by("-modified_at")[:10]
            )
        return context


class OwnDeckListView(LoginRequiredMixin, ListView):
    """ListView to display the own decks."""

    model = Deck
    paginate_by = 24
    template_name = "decks/own_deck_list.html"

    def get_queryset(self) -> QuerySet[Any]:
        qs = super().get_queryset()
        return (
            qs.filter(owner=self.request.user)
            .select_related("hero")
            .order_by("-modified_at")
        )


class DeckDetailView(DetailView):
    """DetailView to display the detail of a Deck model."""

    model = Deck

    def get_queryset(self) -> Manager[Deck]:
        """When retrieving the object, we need to make sure that the Deck is public or
        the User is its owner.

        Returns:
            Manager[Deck]: The view's queryset.
        """
        filter = Q(is_public=True)
        if self.request.user.is_authenticated:
            filter |= Q(owner=self.request.user)
        return Deck.objects.filter(filter).select_related("hero", "owner")

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        """Add metadata of the Deck to the context.

        Returns:
            dict[str, Any]: The view's context.
        """

        context = super().get_context_data(**kwargs)
        context |= get_deck_details(self.object)
        context["form"] = DeckMetadataForm(
            initial={
                "name": self.object.name,
                "description": self.object.description,
                "is_public": self.object.is_public,
            }
        )

        return context


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
        try:
            # If the initial GET request contains the `hero` parameter, insert it into
            # the decklist
            initial["decklist"] = f"1 {self.request.GET['hero']}"
        except KeyError:
            pass
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
        return reverse("deck-detail", kwargs={"pk": self.deck.id})


@login_required
def delete_deck(request: HttpRequest, pk: int) -> HttpResponse:
    try:
        deck = Deck.objects.get(pk=pk)
        if deck.owner == request.user:
            deck.delete()
    except Deck.DoesNotExist:
        pass
    return redirect("own-deck")


@login_required
def update_deck(request: HttpRequest, pk: int) -> HttpResponse:
    """Function to update a deck with AJAX.
    I'm not proud of this implementation, as this code is kinda duplicated in
    `UpdateDeckFormView`. Ideally it should be moved to the API app.

    Args:
        request (HttpRequest): Received request
        pk (int): Id of the target deck

    Returns:
        HttpResponse: A JSON response indicating whether the request succeeded or not.
    """
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    if is_ajax:
        if request.method == "POST":
            try:
                data = json.load(request)
                deck = Deck.objects.get(pk=pk, owner=request.user)
                card = Card.objects.get(reference=data["card_reference"])
                action = data["action"]

                if action == "add":
                    quantity = data["quantity"]
                    CardInDeck.objects.create(deck=deck, card=card, quantity=quantity)
                    status = {"added": True}

                elif action == "delete":
                    if card.type == Card.Type.HERO and deck.hero.reference == card.reference:
                        deck.hero = None
                    else:
                        cid = CardInDeck.objects.get(deck=deck, card=card)
                        cid.delete()
                    status = {"deleted": True}
                else:
                    raise KeyError("Invalid action")

                update_deck_legality(deck)
                deck.save()

            except Deck.DoesNotExist:
                return JsonResponse(
                    {"error": {"code": 404, "message": "Deck not found"}}, status=404
                )
            except (Card.DoesNotExist, CardInDeck.DoesNotExist):
                return JsonResponse(
                    {"error": {"code": 404, "message": "Card not found"}}, status=404
                )
            except (json.decoder.JSONDecodeError, KeyError):
                return JsonResponse(
                    {"error": {"code": 400, "message": "Invalid payload"}}, status=400
                )

            return JsonResponse({"data": status}, status=201)
        else:
            return JsonResponse(
                {"error": {"code": 400, "message": "Invalid request"}}, status=400
            )
    else:
        return HttpResponse("Invalid request", status=400)


class UpdateDeckFormView(LoginRequiredMixin, FormView):
    template_name = "decks/card_list.html"
    form_class = UpdateDeckForm

    def form_valid(self, form: UpdateDeckForm) -> HttpResponse:
        try:
            deck = Deck.objects.get(pk=form.cleaned_data["deck_id"])
            card = Card.objects.get(reference=form.cleaned_data["card_reference"])
            cid = CardInDeck.objects.get(deck=deck, card=card)
            cid.quantity += form.cleaned_data["quantity"]
            cid.save()
        except Deck.DoesNotExist:
            form.add_error("deck_id", "Deck not found")
            return self.form_invalid(form)
        except Card.DoesNotExist:
            form.add_error("card_reference", "Card not found")
            return self.form_invalid(form)
        except CardInDeck.DoesNotExist:
            # The card is not in the deck, so we add it
            CardInDeck.objects.create(
                deck=deck, card=card, quantity=form.cleaned_data["quantity"]
            )

        update_deck_legality(deck)
        deck.save()

        return super().form_valid(form)

    def get_success_url(self) -> str:
        return f"{reverse_lazy('cards')}?{self.request.META['QUERY_STRING']}"


class UpdateDeckMetadataFormView(LoginRequiredMixin, FormView):
    template_name = "decks/deck_detail.html"
    form_class = DeckMetadataForm

    def form_valid(self, form: DeckMetadataForm) -> HttpResponse:
        try:
            deck = Deck.objects.get(pk=self.kwargs["pk"], owner=self.request.user)
            deck.name = form.cleaned_data["name"]
            deck.description = form.cleaned_data["description"]
            deck.is_public = form.cleaned_data["is_public"]
            deck.save()
        except Deck.DoesNotExist:
            # form.add_error(None, "Invalid permissions")
            # return self.form_invalid(form)
            pass

        return super().form_valid(form)

    def form_invalid(self, form: Any) -> HttpResponse:
        # UpdateDeckMetadataFormView.kwargs["pk"] = self.kwargs["pk"]
        # return redirect(self.get_success_url(), kwargs=self.get_context_data(form=form))
        return super().form_invalid(form)

    def get_success_url(self) -> str:
        """Return the redirect URL for a successful Deck submission.
        Redirect to the Deck's detail view.

        Returns:
            str: The Deck's detail endpoint.
        """
        return reverse("deck-detail", kwargs={"pk": self.kwargs["pk"]})


class CardListView(ListView):
    model = Card
    paginate_by = 24

    def get_queryset(self) -> QuerySet[Any]:
        qs = super().get_queryset()
        filters = Q()

        query = self.request.GET.get("query")
        if query:
            filters &= Q(name__icontains=query)

        factions = self.request.GET.get("faction")
        if factions:
            try:
                factions = [Card.Faction(faction) for faction in factions.split(",")]
            except ValueError:
                pass
            else:
                filters &= Q(faction__in=factions)

        rarities = self.request.GET.get("rarity")
        if rarities:
            try:
                rarities = [Card.Rarity(rarity) for rarity in rarities.split(",")]
            except ValueError:
                pass
            else:
                filters &= Q(rarity__in=rarities)

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

        return qs.filter(filters)

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context["own_decks"] = Deck.objects.filter(
                owner=self.request.user
            ).order_by("-modified_at")
            context["form"] = UpdateDeckForm()

        checked_filters = []
        for filter in ["faction", "rarity", "type"]:
            if filter in self.request.GET:
                checked_filters += self.request.GET[filter].split(",")
        context["checked_filters"] = checked_filters
        if "query" in self.request.GET:
            context["query"] = self.request.GET.get("query")

        return context
