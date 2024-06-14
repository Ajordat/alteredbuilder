from django.http import HttpRequest


class TroubleshootingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):

        response = self.get_response(request)

        return response
