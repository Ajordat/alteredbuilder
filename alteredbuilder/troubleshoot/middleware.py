
from django.http import HttpRequest
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin


class TroubleshootingMiddleware(MiddlewareMixin):
    def process_request(self, request: HttpRequest):
        
        if request.path not in [reverse("troubleshoot:session")]:
            return
        print(f"{request.path=}")
        print(f"{request.user.username=}")
        print(f"{request.session.session_key=}")
        print(f"{request.COOKIES}")
        try:
            print(f"{request.session["_auth_user_id"]=}")
        except KeyError:
            print("No key `_auth_user_id`")