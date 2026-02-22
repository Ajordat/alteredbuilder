from collections import defaultdict
from http import HTTPMethod, HTTPStatus
import json

from django.conf import settings
from django.db.models import Case, IntegerField, Q, When
from django.http import HttpRequest, JsonResponse
from django.utils.translation import gettext_lazy as _

from decks.deck_utils import card_code_from_reference, family_code_from_reference
from decks.game_modes import StandardGameMode
from decks.models import Card
from decks.templatetags.deck_styles import cdn_image_url
from recommender.model_utils import RecommenderHelper


RECOMMENDATIONS_COUNT = 5


def get_next_card(request: HttpRequest) -> JsonResponse:
    if request.method != HTTPMethod.POST:
        return JsonResponse(
            {"error": "Only POST requests are allowed", "human_readable": False},
            status=HTTPStatus.METHOD_NOT_ALLOWED,
        )

    if not request.user.is_authenticated:
        return JsonResponse(
            {
                "error": _("Login into the platform to use the recommender!"),
                "human_readable": True,
            },
            status=HTTPStatus.FORBIDDEN,
        )

    try:
        # Parse the request
        data = json.loads(request.body)
        hero = card_code_from_reference(data["hero"])
        faction = data["faction"]
        decklist = defaultdict(int)
        decklist_family_codes = defaultdict(int)
        for reference, quantity in data["decklist"].items():
            decklist[card_code_from_reference(reference)] += quantity
            decklist_family_codes[family_code_from_reference(reference)] += quantity

        # Load model
        model = RecommenderHelper.load_model(faction)
        if not model:
            return JsonResponse(
                {
                    "error": _(
                        "Model for this faction is not available. No recommendations can be given."
                    ),
                    "human_readable": True,
                },
                status=HTTPStatus.NOT_FOUND,
            )

        # Prepare to query the model
        RecommenderHelper.build_card_pool()
        try:
            deck_vector = RecommenderHelper.generate_vector_for_deck(
                cards=decklist, faction=faction, hero=hero
            )
        except ValueError:
            return JsonResponse(
                {
                    "error": _("The deck contains an unexpected card."),
                    "human_readable": True,
                },
                status=HTTPStatus.BAD_REQUEST,
            )

        # Obtain recommendations
        recommended_cards = RecommenderHelper.get_recommended_cards(
            model, deck_vector, faction, RECOMMENDATIONS_COUNT
        )

        # Filter cards (cards already in the deck or the max family count has been reached)
        filtered_cards = []
        for card in recommended_cards:
            family_code = "_".join(card.split("_")[:-1])
            if (
                family_code in decklist_family_codes
                and decklist_family_codes[family_code]
                >= StandardGameMode.MAX_SAME_FAMILY_CARD_COUNT
            ):
                continue
            filtered_cards.append(card)

        if not filtered_cards:
            return JsonResponse({"recommended_cards": []}, status=HTTPStatus.OK)

        query = Q()
        order_cases = []
        for index, reference in enumerate(filtered_cards):
            query |= Q(reference__contains=reference, faction=faction)
            order_cases.append(When(reference__contains=reference, then=index))

        object_cards = (
            Card.objects.filter(query)
            .annotate(order=Case(*order_cases, output_field=IntegerField()))
            .exclude(rarity=Card.Rarity.UNIQUE)
            .exclude(set__code="COREKS")
            .exclude(is_alt_art=True)
            .exclude(is_promo=True)
            .order_by("order")
        )

        filtered_cards = []
        for card in object_cards:

            filtered_cards.append(
                {
                    "reference": card.reference,
                    "image": cdn_image_url(card.image_url),
                    "name": card.name,
                    "type": card.type,
                    "rarity": card.rarity,
                    "family": card.get_card_code(),
                }
            )
        # Return the recommendations as a response
        return JsonResponse({"recommended_cards": filtered_cards}, status=HTTPStatus.OK)

    except json.JSONDecodeError:
        return JsonResponse(
            {"error": "Invalid JSON data", "human_readable": False},
            status=HTTPStatus.BAD_REQUEST,
        )
    except Exception as e:
        if settings.DEBUG:
            raise e
        return JsonResponse(
            {"error": str(e), "human_readable": False},
            status=HTTPStatus.INTERNAL_SERVER_ERROR,
        )
