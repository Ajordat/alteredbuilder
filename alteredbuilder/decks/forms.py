import re

from django import forms
from django.core.validators import RegexValidator


decklist_validator = RegexValidator(r"^[123] \w+$", flags=re.MULTILINE)


class DecklistForm(forms.Form):
    name = forms.CharField(label="deck-name", max_length=50, required=True)
    decklist = forms.CharField(
        label="decklist",
        widget=forms.Textarea,
        max_length=1000,
        required=True,
        validators=[decklist_validator],
    )
    is_public = forms.BooleanField(required=False)
