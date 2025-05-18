from datetime import datetime, timezone
from http import HTTPStatus
from http.cookies import SimpleCookie
import re

from django.core.management.base import CommandError
from django.utils.http import urlencode
from django.utils.timezone import make_aware
import requests

from config.commands import BaseCommand
from config.utils import get_user_agent
from external.models import AccessToken, Cookie

TOKEN_DOMAIN = "altered.gg"


class Command(BaseCommand):
    help = "Refresh the access token and store it along with valid cookies."

    def handle(self, *args, **kwargs):

        # Refresh the access token
        headers = {
            "Cookie": self.build_request_cookies(),
            "User-Agent": get_user_agent("refresh_token"),
        }
        response = requests.get(
            "https://www.altered.gg/api/auth/session", headers=headers
        )

        if response.status_code != HTTPStatus.OK:
            raise CommandError(f"Request failed with status {response.status_code}")

        # Update the access token
        self.update_access_token(response.json())

        # Extract cookies from the response and store them
        self.update_cookies(response.headers)

        self.stdout.write("Access token refreshed and stored successfully.")

    def build_request_cookies(self):
        # Retrieve cookie from db
        cookies = Cookie.objects.filter(service=TOKEN_DOMAIN)
        if not cookies:
            raise CommandError("No cookies found")

        # Extract valid cookies
        valid_cookie_headers = [
            urlencode({"__Secure-next-auth.callback-url": "https://www.altered.gg"})
        ]

        for cookie in cookies:
            if not cookie.expires or cookie.expires > datetime.now(timezone.utc):
                valid_cookie_headers.append(f"{cookie.name}={cookie.value}")

        if not valid_cookie_headers:
            raise CommandError("No valid cookies found")

        # Return the valid cookies as a single string
        return "; ".join(valid_cookie_headers)

    def update_access_token(self, response: dict):
        access_token = response.get("accessToken")
        expires = response.get("expires")

        if not access_token or not expires:
            raise CommandError("Access token or expiry not found in session response")

        AccessToken.objects.get_or_create(
            service=TOKEN_DOMAIN,
            defaults={"token": access_token, "expires_at": expires},
        )

    def update_cookies(self, headers: dict):
        all_cookies = self.extract_cookies_from_response(headers)
        for header in all_cookies:
            cookie = SimpleCookie()
            cookie.load(header)
            for morsel in cookie.values():
                if not morsel.key.startswith("__Secure-next-auth.session-token"):
                    continue

                expiration_date = None
                if "expires" in morsel:
                    expiration_date = make_aware(
                        datetime.strptime(
                            morsel["expires"], "%a, %d %b %Y %H:%M:%S %Z"
                        ),
                        timezone=timezone.utc,
                    )

                Cookie.objects.update_or_create(
                    service=TOKEN_DOMAIN,
                    name=morsel.key,
                    defaults={
                        "value": morsel.value,
                        "expires": expiration_date,
                    },
                )

    def extract_cookies_from_response(self, headers: dict):
        set_cookie_headers = headers.get("Set-Cookie")
        if not set_cookie_headers:
            raise CommandError("No Set-Cookie header found in response.")

        if isinstance(set_cookie_headers, str):
            set_cookie_headers = [set_cookie_headers]

        all_cookies = []
        # We need to do this because it seems that instead of multiple Set-Cookie headers,
        # we get a single header with multiple cookies separated by ', '.
        # However, I'm afraid that the API might change this in the future. So basically,
        # we iterate all the Set-Cookie headers and split them.
        for cookie in set_cookie_headers:
            # Split on ', ' only when it is followed by a cookie name (not inside a value)
            all_cookies += re.split(r", (?=[^ ;]+=)", cookie)

        return all_cookies
