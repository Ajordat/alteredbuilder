from http import HTTPStatus
import json

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import F, Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from api.utils import ajax_request, ApiJsonResponse
from decks.deck_utils import patch_deck, remove_card_from_deck
from decks.game_modes import update_deck_legality
from decks.models import Card, CardInDeck, Deck, LovePoint
from decks.forms import DeckMetadataForm, DeckTagsForm


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
