from http import HTTPStatus
import json

from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.translation import activate, get_language, gettext_lazy as _


def ajax_request(methods=None):
    def wrap(func):
        def inner(request: HttpRequest, *args, **kwargs):

            is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
            if is_ajax:
                if request.method in (methods or ["POST"]):
                    try:
                        return func(request, *args, **kwargs)
                    except json.decoder.JSONDecodeError:
                        return ApiJsonResponse(
                            _("Invalid payload"), HTTPStatus.BAD_REQUEST
                        )
                else:
                    return ApiJsonResponse(_("Invalid request"), HTTPStatus.BAD_REQUEST)
            else:
                return HttpResponse(_("Invalid request"), status=HTTPStatus.BAD_REQUEST)

        return inner

    return wrap


def locale_agnostic(func):
    def inner(*args, **kwargs):
        current_language = get_language()
        try:
            activate(settings.LANGUAGE_CODE)
            result = func(*args, **kwargs)
        finally:
            activate(current_language)
        return result

    return inner


class ApiJsonResponse(JsonResponse):
    def __init__(self, data, status_code, *args, **kwargs):
        if status_code >= HTTPStatus.BAD_REQUEST:
            msg = {"error": {"code": status_code, "message": data}}
        else:
            msg = {"data": data}
        super().__init__(msg, *args, status=status_code, **kwargs)
