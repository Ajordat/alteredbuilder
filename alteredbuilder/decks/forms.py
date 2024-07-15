import re

from django import forms
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

from .models import Deck

# Form definitions

# Regex to validate whether at least one line follows the correct format
decklist_validator = RegexValidator(r"^\d+ \w+$", flags=re.MULTILINE)


class DecklistForm(forms.Form):
    """Form to validate the creation of a Deck."""

    template_name = "forms/submit_decklist.html"
    name = forms.CharField(
        label="deck-name",
        max_length=Deck._meta.get_field("name").max_length,
        required=True,
    )
    description = forms.CharField(
        label=_("description"),
        widget=forms.Textarea,
        max_length=Deck._meta.get_field("description").max_length,
        required=False,
    )
    decklist = forms.CharField(
        label=_("decklist"),
        widget=forms.Textarea,
        max_length=2000,
        required=True,
        validators=[decklist_validator],
        error_messages={
            "invalid": _(
                "Each line should be a quantity (1, 2 or 3) and a card reference."
            )
        },
    )
    is_public = forms.BooleanField(required=False)


class DeckMetadataForm(forms.Form):
    """Form to validate the update of a Deck's metadata."""

    template_name = "forms/submit_deck_metadata.html"
    name = forms.CharField(
        label="deck-name",
        max_length=Deck._meta.get_field("name").max_length,
        required=True,
    )
    description = forms.CharField(
        label=_("description"),
        widget=forms.Textarea,
        max_length=Deck._meta.get_field("description").max_length,
        required=False,
    )
    is_public = forms.BooleanField(required=False)
