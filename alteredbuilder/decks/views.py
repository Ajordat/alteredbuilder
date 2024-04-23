from collections import defaultdict
from typing import Any
import json

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from django.db.models.manager import Manager
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.urls import reverse, reverse_lazy
from django.views.generic.detail import DetailView
from django.views.generic.edit import FormView
from django.views.generic.list import ListView

from .game_modes import GameMode, StandardGameMode
from .models import Card, CardInDeck, Deck, Hero
from .forms import DecklistForm, UpdateDeckForm
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
    paginate_by = 10

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
                .order_by("-modified_at")
            )
        return context


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
        decklist = (
            self.object.cardindeck_set.select_related(
                "card__character", "card__spell", "card__permanent"
            )
            .order_by("card__reference")
            .all()
        )

        hand_counter = defaultdict(int)
        recall_counter = defaultdict(int)
        rarity_counter = defaultdict(int)

        # This dictionary will hold all metadata based on the card's type by using the
        # type as a key
        d = {
            Card.Type.CHARACTER: [[], 0, "character"],
            Card.Type.SPELL: [[], 0, "spell"],
            Card.Type.PERMANENT: [[], 0, "permanent"],
        }
        for cid in decklist:
            # Append the card to its own type card list
            d[cid.card.type][0].append((cid.quantity, cid.card))
            # Count the card count of the card's type
            d[cid.card.type][1] += cid.quantity
            # Count the amount of cards with the same hand cost
            hand_counter[
                getattr(cid.card, d[cid.card.type][2]).main_cost
            ] += cid.quantity
            # Count the amount of cards with the same recall cost
            recall_counter[
                getattr(cid.card, d[cid.card.type][2]).recall_cost
            ] += cid.quantity
            # Count the amount of cards with the same rarity
            rarity_counter[cid.card.rarity] += cid.quantity

        decklist_text = f"1 {self.object.hero.reference}\n"
        decklist_text += "\n".join(
            [f"{cid.quantity} {cid.card.reference}" for cid in decklist]
        )
        context |= {
            "decklist": decklist_text,
            "character_list": d[Card.Type.CHARACTER][0],
            "spell_list": d[Card.Type.SPELL][0],
            "permanent_list": d[Card.Type.PERMANENT][0],
            "stats": {
                "type_distribution": {
                    "characters": d[Card.Type.CHARACTER][1],
                    "spells": d[Card.Type.SPELL][1],
                    "permanents": d[Card.Type.PERMANENT][1],
                },
                "total_count": d[Card.Type.CHARACTER][1]
                + d[Card.Type.SPELL][1]
                + d[Card.Type.PERMANENT][1],
                "mana_distribution": {
                    "hand": hand_counter,
                    "recall": recall_counter,
                },
                "rarity_distribution": {
                    "common": rarity_counter[Card.Rarity.COMMON],
                    "rare": rarity_counter[Card.Rarity.RARE],
                    "unique": rarity_counter[Card.Rarity.UNIQUE],
                },
            },
            "legality": {
                "standard": {
                    "is_legal": self.object.is_standard_legal,
                    "errors": GameMode.ErrorCode.from_list_to_user(
                        self.object.standard_legality_errors, StandardGameMode
                    ),
                }
            },
        }

        return context


@transaction.atomic
def create_new_deck(user: User, deck_form: dict) -> Deck:
    """Method to validate the clean data from a DecklistForm and create it if all input
    is valid.

    Args:
        user (User): The Deck's owner.
        deck_form (dict): Clean data from a DecklistForm.

    Raises:
        MalformedDeckException: If the decklist is invalid.

    Returns:
        Deck: The resulting object.
    """
    decklist = deck_form["decklist"]
    deck = Deck.objects.create(
        name=deck_form["name"],
        owner=user,
        is_public=deck_form["is_public"],
        description=deck_form["description"],
    )
    has_hero = False

    total_count = 0
    rare_count = 0
    unique_count = 0
    factions = []

    for line in decklist.splitlines():
        # For each line it is needed to:
        # * Validate its format
        # * Search the card reference on the database
        #   - If it's a Hero, assign it to the Deck's Hero
        #   - Otherwise append it to the list of cards
        try:
            count, reference = line.split()
            count = int(count)
        except ValueError:
            # The form validator only checks if there's at least one
            # line with the correct format
            raise MalformedDeckException(f"Failed to unpack '{line}'")

        try:
            card = Card.objects.get(reference=reference)
            if card.faction not in factions:
                factions.append(card.faction)
        except Card.DoesNotExist:
            # The Card's reference needs to exist on the database
            raise MalformedDeckException(f"Card '{reference}' does not exist")

        if card.type == Card.Type.HERO:
            if not has_hero:
                try:
                    deck.hero = Hero.objects.get(reference=reference)
                except Hero.DoesNotExist:
                    # This situation would imply a database inconsistency
                    raise MalformedDeckException(f"Card '{reference}' does not exist")
                has_hero = True
            else:
                # The Deck model requires to have exactly one Hero per Deck
                raise MalformedDeckException("Multiple heroes present in the decklist")
        else:
            # Link the Card with the Deck
            CardInDeck.objects.create(deck=deck, card=card, quantity=count)

            total_count += count
            if card.rarity == Card.Rarity.RARE:
                rare_count += count
            elif card.rarity == Card.Rarity.UNIQUE:
                unique_count += count

    error_list = StandardGameMode.validate(
        **{
            "faction_count": len(factions),
            "total_count": total_count,
            "rare_count": rare_count,
            "unique_count": unique_count,
        }
    )
    deck.is_standard_legal = not bool(error_list)
    deck.standard_legality_errors = error_list
    deck.save()

    if not has_hero:
        # The Deck model requires to have exactly one Hero per Deck
        raise MalformedDeckException("Missing hero in decklist")

    return deck


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
            data = json.load(request)
            try:
                deck = Deck.objects.get(pk=pk, owner=request.user)
                card = Card.objects.get(reference=data["card_reference"])
                action = data["action"]

                if action == "add":
                    quantity = data["quantity"]
                    CardInDeck.objects.create(deck=deck, card=card, quantity=quantity)

                elif action == "delete":
                    cid = CardInDeck.objects.get(deck=deck, card=card)
                    cid.delete()

                deck.save()

            except Deck.DoesNotExist:
                return JsonResponse(
                    {"error": {"code": 404, "message": "Deck not found"}}, status=404
                )
            except Card.DoesNotExist:
                return JsonResponse(
                    {"error": {"code": 404, "message": "Card not found"}}, status=404
                )
            except KeyError:
                return JsonResponse(
                    {"error": {"code": 400, "message": "Invalid payload"}}, status=400
                )

            return JsonResponse({"data": {"deleted": True}}, status=201)
        else:
            return JsonResponse(
                {"error": {"code": 400, "message": "Invalid request"}}, status=400
            )
    else:
        return HttpResponse("Invalid request", status=400)


class UpdateDeckFormView(LoginRequiredMixin, FormView):
    template_name = "decks/card_list.html"
    form_class = UpdateDeckForm
    success_url = reverse_lazy("cards")

    def form_valid(self, form: UpdateDeckForm) -> HttpResponse:
        deck = Deck.objects.get(pk=form.cleaned_data["deck_id"])
        card = Card.objects.get(reference=form.cleaned_data["card_reference"])
        try:
            cid = CardInDeck.objects.get(deck=deck, card=card)
            cid.quantity += form.cleaned_data["quantity"]
            cid.save()
        except CardInDeck.DoesNotExist:
            # The card is not in the deck, so we add it
            CardInDeck.objects.create(
                deck=deck, card=card, quantity=form.cleaned_data["quantity"]
            )

        # Force the update of the `modified_at` field
        deck.save()

        return super().form_valid(form)


class CardListView(ListView):
    model = Card
    paginate_by = 24

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context["own_decks"] = Deck.objects.filter(
                owner=self.request.user
            ).order_by("-modified_at")
            context["form"] = UpdateDeckForm()
        return context
