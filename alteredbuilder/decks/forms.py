import re

from django import forms
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

from decks.models import Card, Comment, Deck, Tag


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
    copy_of = forms.CharField(required=False)
    decklist = forms.CharField(
        label=_("decklist"),
        widget=forms.Textarea,
        max_length=2000,
        required=True,
        validators=[RegexValidator(r"^\d+ \w+$", flags=re.MULTILINE)],
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


class DeckTagsForm(forms.Form):
    """Form to create or modify the Tags of a Deck."""

    template_name = "forms/submit_deck_tags.html"

    primary_tags = forms.ModelChoiceField(
        queryset=Tag.objects.filter(type=Tag.Type.TYPE).order_by("pk"),
        widget=forms.RadioSelect,
        required=False,
    )
    secondary_tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.filter(type=Tag.Type.SUBTYPE),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )


class CommentForm(forms.Form):
    """Form to create a Comment on a Deck."""

    template_name = "forms/submit_comment.html"
    body = forms.CharField(
        label="body",
        max_length=Comment._meta.get_field("body").max_length,
        required=True,
    )


class CardImportForm(forms.Form):
    """Form to import a Card of unique rarity into the database."""

    reference = forms.CharField(
        label=_("Card Reference"),
        max_length=Card._meta.get_field("reference").max_length,
        validators=[
            RegexValidator(
                r"^ALT_[A-Z]{4,7}_(?:B|P|A)_[A-Z]{2}_\d{2}_U_\d+$",
                _(
                    "Invalid value. The reference should look similar to 'ALT_COREKS_B_OR_21_U_2139'."
                ),
            )
        ],
    )


class ChangeDeckOwnerForm(forms.Form):
    new_owner = forms.ModelChoiceField(
        queryset=get_user_model().objects.all(), label="New Owner"
    )
