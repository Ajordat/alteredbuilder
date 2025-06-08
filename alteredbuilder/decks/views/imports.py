from http import HTTPMethod, HTTPStatus
import json
from typing import Any

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from django.views.generic.edit import FormView

from api.utils import ApiJsonResponse
from decks.deck_utils import create_new_deck, import_unique_card
from decks.models import Card, DeckCopy, FavoriteCard
from decks.forms import CardImportForm, DecklistForm
from decks.exceptions import AlteredAPIError, CardAlreadyExists, MalformedDeckException


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

        initial["copy_of"] = self.request.GET.get("source", "")

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
            data = form.cleaned_data
            self.deck = create_new_deck(self.request.user, data)
            if data["copy_of"]:
                DeckCopy.objects.create(
                    source_deck_id=data["copy_of"], target_deck=self.deck
                )

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
def import_card(request: HttpRequest) -> HttpResponse:
    """Receive the reference of a unique card and import it into the database.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The response object.
    """
    context = {}
    form = None
    if request.method == HTTPMethod.POST:
        form = CardImportForm(request.POST)
        if form.is_valid():
            reference = form.cleaned_data["reference"]
            try:
                context |= import_card_by_reference(reference, request.user)
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


@login_required
@require_POST
def import_multiple_cards(request: HttpRequest) -> HttpResponse:
    """Receive the reference of a unique card and import it into the database.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The response object.
    """
    success = []
    failure = []

    try:
        data = json.loads(request.body)
    except json.decoder.JSONDecodeError:
        return ApiJsonResponse("Missing body", HTTPStatus.BAD_REQUEST)

    if "references" not in data:
        return ApiJsonResponse("Missing references", HTTPStatus.BAD_REQUEST)

    references = data["references"]

    for reference in references:
        try:
            import_card_by_reference(reference, request.user)
            success.append(reference)
        except AlteredAPIError:
            failure.append(reference)

    return ApiJsonResponse({"success": success, "failure": failure}, HTTPStatus.OK)


def import_card_by_reference(reference: str, user: User):
    try:
        # Attempt to import a unique card
        card = import_unique_card(reference)
        # Automatically favorite the card
        FavoriteCard.objects.get_or_create(user=user, card=card)

        # Fill the context
        message = _(
            "The card '%(card_name)s' (%(reference)s) was successfully imported."
        ) % {"card_name": card.name, "reference": reference}
    except CardAlreadyExists:
        # If the card already exists, inform the user
        card = Card.objects.get(reference=reference)
        # Automatically favorite the card if it wasn't already
        FavoriteCard.objects.get_or_create(user=user, card=card)

        # Fill the context
        message = _(
            "This unique version of '%(card_name)s' (%(reference)s) already exists in the database."
        ) % {"card_name": card.name, "reference": reference}

    return {"message": message, "card": card}
