from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import numpy as np

from recommender.model_utils import ModelHelper
from recommender.models import TrainedModel, Card


@csrf_exempt  # Exempt from CSRF for testing; add proper CSRF handling in production
def get_recommendations_view(request, faction):
    if request.method == "POST":
        try:
            # Parse the received JSON data
            data = json.loads(request.body)

            # Load the model for the given faction
            model = ModelHelper.load_model(faction)
            if not model:
                return JsonResponse(
                    {"error": "Model for this faction is not available"}, status=404
                )

            ModelHelper.build_card_pool()
            deck_vector = ModelHelper.generate_vector_for_deck(
                cards=data["decklist"], faction=faction, hero=data["hero"]
            )

            recommended_card_ids = ModelHelper.get_recommended_cards(
                model, deck_vector, faction
            )

            # Get the card details from the database based on recommended card IDs
            recommended_cards = Card.objects.filter(id__in=recommended_card_ids)
            recommended_card_names = [card.name for card in recommended_cards]
            print(recommended_card_names)

            # Return the recommendations as a response
            return JsonResponse(
                {"recommended_cards": recommended_card_names}, status=200
            )

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Only POST requests are allowed"}, status=405)
