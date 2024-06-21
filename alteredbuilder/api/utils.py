import json

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.translation import gettext_lazy as _


def ajax_request(func):
    def inner(request: HttpRequest, *args, **kwargs):

        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
        if is_ajax:
            if request.method == "POST":
                try:
                    return func(request, *args, **kwargs)
                except json.decoder.JSONDecodeError:
                    return ApiJsonResponse(_("Invalid payload"), 400)
            else:
                return ApiJsonResponse(_("Invalid request"), 400)
        else:
            return HttpResponse(_("Invalid request"), status=400)

    return inner


class ApiJsonResponse(JsonResponse):
    def __init__(self, data, status_code, *args, **kwargs):
        if status_code >= 400:
            msg = {"error": {"code": status_code, "message": data}}
        else:
            msg = {"data": data}
        super().__init__(msg, *args, status=status_code, **kwargs)
