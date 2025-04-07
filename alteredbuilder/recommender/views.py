from http import HTTPStatus
import json

from django.conf import settings
from django.db.models import Case, IntegerField, Q, When
from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from decks.deck_utils import card_code_from_reference
from decks.models import Card
from decks.templatetags.deck_styles import cdn_image_url
from recommender.model_utils import RecommenderHelper


@csrf_exempt
def get_next_card(request: HttpRequest) -> JsonResponse:
    if request.method == "POST":
        try:
            # Parse the request
            data = json.loads(request.body)
            hero = card_code_from_reference(data["hero"])
            faction = data["faction"]
            decklist = {
                card_code_from_reference(k): v for k, v in data["decklist"].items()
            }

            # Load model
            model = RecommenderHelper.load_model(faction)
            if not model:
                return JsonResponse(
                    {"error": "Model for this faction is not available"},
                    status=HTTPStatus.NOT_FOUND,
                )

            # Prepare to query the model
            RecommenderHelper.build_card_pool()
            deck_vector = RecommenderHelper.generate_vector_for_deck(
                cards=decklist, faction=faction, hero=hero
            )

            # Obtain recommendations
            recommended_cards = RecommenderHelper.get_recommended_cards(
                model, deck_vector, faction
            )

            query = Q()
            order_cases = []
            for index, (reference, rarity) in enumerate(recommended_cards):
                query |= Q(
                    reference__contains=reference, rarity=rarity, faction=faction
                )
                order_cases.append(
                    When(reference__contains=reference, rarity=rarity, then=index)
                )

            recommended_cards = (
                Card.objects.filter(query)
                .annotate(order=Case(*order_cases, output_field=IntegerField()))
                .exclude(set__code="COREKS")
                .exclude(is_alt_art=True)
                .order_by("order")
            )
            recommended_card_names = [
                {
                    "reference": card.reference,
                    "image": cdn_image_url(card.image_url),
                    "name": card.name,
                    "type": card.type,
                    "rarity": card.rarity,
                    "family": card.get_card_code(),
                }
                for card in recommended_cards
                if card.reference not in data["decklist"].keys()
            ]

            # Return the recommendations as a response
            return JsonResponse(
                {"recommended_cards": recommended_card_names}, status=HTTPStatus.OK
            )

        except json.JSONDecodeError:
            return JsonResponse(
                {"error": "Invalid JSON data"}, status=HTTPStatus.BAD_REQUEST
            )
        except Exception as e:
            if settings.DEBUG:
                raise e
            return JsonResponse(
                {"error": str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR
            )
    else:
        return JsonResponse(
            {"error": "Only POST requests are allowed"},
            status=HTTPStatus.METHOD_NOT_ALLOWED,
        )
