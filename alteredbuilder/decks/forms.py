import re

from django import forms
from django.core.validators import RegexValidator

# Form definitions

# Regex to validate whether at least one line follows the correct format
decklist_validator = RegexValidator(r"^[123] \w+$", flags=re.MULTILINE)


class DecklistForm(forms.Form):
    """Form to validate the creation of a Deck."""

    template_name = "forms/submit_decklist.html"
    name = forms.CharField(label="deck-name", max_length=50, required=True)
    description = forms.CharField(
        label="description", widget=forms.Textarea, max_length=1000, required=False
    )
    decklist = forms.CharField(
        label="decklist",
        widget=forms.Textarea,
        max_length=1000,
        required=True,
        validators=[decklist_validator],
        error_messages={
            "invalid": "Each line should be a quantity (1, 2 or 3) and a card reference."
        },
    )
    is_public = forms.BooleanField(required=False)
