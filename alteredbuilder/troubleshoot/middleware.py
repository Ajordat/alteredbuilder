
from django.http import HttpRequest
from django.urls import reverse
from django.utils.http import urlencode


class TroubleshootingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):

        response = self.get_response(request)

        if "Location" in response.headers and "X-Forwarded-Host" in request.headers:
            url_location = response.headers["Location"]
            url = []
            for url_fragment in url_location.split("&"):
                if url_fragment.startswith("redirect_uri"):
                    url += [urlencode({"redirect_uri": f"https://{request.headers["X-Forwarded-Host"]}/accounts/discord/login/callback/"})]
                else:
                    url += [url_fragment]
            # response.headers["Location"] = "&".join(url)

        return response