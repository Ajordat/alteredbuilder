from typing import Type

from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import render
from django.views.decorators.clickjacking import xframe_options_exempt

from decks.models import Card, Deck


@xframe_options_exempt
def deck_embed_view(request, deck_id):
    try:
        deck = Deck.objects.get(pk=deck_id)
    except Deck.DoesNotExist:
        raise Http404("Deck does not exist")

    if not deck.is_public:
        raise PermissionDenied

    params: dict = request.GET

    return render(
        request,
        "decks/embed_deck.html",
        {
            "deck": {
                "metadata": deck,
                "characters": deck.cardindeck_set.filter(card__type=Card.Type.CHARACTER)
                .select_related("card")
                .order_by("card__stats__main_cost", "card__stats__recall_cost"),
                "spells": deck.cardindeck_set.filter(card__type=Card.Type.SPELL)
                .select_related("card")
                .order_by("card__stats__main_cost", "card__stats__recall_cost"),
                "permanents": deck.cardindeck_set.filter(
                    card__type__in=[
                        Card.Type.LANDMARK_PERMANENT,
                        Card.Type.EXPEDITION_PERMANENT,
                    ]
                )
                .select_related("card")
                .order_by("card__stats__main_cost", "card__stats__recall_cost"),
            },
            "view": {
                "columns": safe_params(params, "columns", int, 2),
                "display_height": safe_params(params, "display_height", int, 300),
                "section_box": safe_params(params, "section_box", bool, False),
                "hover_display": safe_params(params, "hover_display", bool, True),
                "hover_animation": safe_params(params, "hover_animation", bool, True),
                "show_name": safe_params(params, "show_name", bool, True),
                "show_author": safe_params(params, "show_author", bool, True),
                "transparent_body": safe_params(
                    params, "transparent_body", bool, False
                ),
                "shadow_body": safe_params(params, "shadow_body", bool, True),
            },
        },
    )


def safe_params[T](params: dict, key: str, cast: Type[T], default: T = None) -> T:
    value = params.get(key, default)
    try:
        if cast is bool:
            str_value = str(value).lower()
            if str_value in ("true", "1"):
                return True
            elif str_value in ("false", "0"):
                return False
            return default
        return cast(value)
    except (ValueError, TypeError):
        return default
