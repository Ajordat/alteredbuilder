from http import HTTPStatus
import json

from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from api.utils import ApiJsonResponse, ajax_request
from decks.models import Set


def display_collection(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "decks/collection.html",
        {"card_sets": Set.objects.exclude(code="COREKS").order_by("-release_date")},
    )


@ajax_request()
def save_collection(request: HttpRequest):
    if not request.user.is_authenticated:
        raise PermissionDenied

    form = json.loads(request.body)

    if "collection" not in form:
        return ApiJsonResponse({"success": False}, HTTPStatus.BAD_REQUEST)

    request.user.profile.collection = form["collection"]
    request.user.profile.save()

    return ApiJsonResponse({"success": True}, HTTPStatus.OK)
