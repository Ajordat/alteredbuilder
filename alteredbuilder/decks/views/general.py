import json
import os

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def deck_legality_view(request: HttpRequest) -> HttpResponse:
    json_path = os.path.join(os.path.dirname(__file__), "data", "legality.json")

    with open(json_path, "r", encoding="utf-8") as json_file:
        data = json.load(json_file)

    last_update_date = data.get("last_update", "Unknown date")
    patches = data.get("patches", [])

    return render(
        request,
        "decks/legality_changelog.html",
        {"last_update_date": last_update_date, "patches": patches},
    )
