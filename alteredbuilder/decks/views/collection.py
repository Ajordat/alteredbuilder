from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from decks.models import Set


def display_collection(request: HttpRequest) -> HttpResponse:

    return render(
        request,
        "decks/collection.html",
        {"card_sets": Set.objects.exclude(code="COREKS").order_by("-release_date")},
    )
