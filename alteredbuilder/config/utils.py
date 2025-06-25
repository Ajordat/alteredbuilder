from http import HTTPStatus
import json
import math
import random
import time
from typing import Any, Generator
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings

from decks.exceptions import AlteredAPIError

LOCALE_IRREGULAR_CODES = {"en": "en-us"}


def get_user_agent(task: str) -> str:
    return settings.USER_AGENT_BASE.format(task)


def altered_api_paginator(
    endpoint: str,
    user_agent_task,
    params: list[tuple[str, str]] = None,
    locale: str = "en-us",
    auth_token: bool = False,
) -> Generator[dict[str, Any], None, None]:
    headers = {
        "Accept-Language": locale,
        "User-Agent": get_user_agent(user_agent_task),
    }
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"

    page_index = 1
    page_count = math.inf
    total_items = math.inf

    url = f"{settings.ALTERED_API_BASE_URL}{endpoint}"

    while page_index <= page_count:
        query_params = f"?page={page_index}&itemsPerPage={settings.ALTERED_API_ITEMS_PER_PAGE}&locale={locale}"
        if params:
            query_params += "&" + "&".join([f"{k}={v}" for k, v in params])

        # Query the API
        data = fetch_with_backoff(url + query_params, headers)

        total_items = min(data["hydra:totalItems"], total_items)
        page_count = min(
            math.ceil(total_items / settings.ALTERED_API_ITEMS_PER_PAGE), page_count
        )

        for item in data["hydra:member"]:
            yield item

        page_index += 1


def fetch_with_backoff(url, headers, max_retries=5):
    for attempt in range(max_retries):
        try:
            with urlopen(Request(url, headers=headers)) as response:
                return json.loads(response.read().decode("utf8"))
        except HTTPError as e:
            if attempt + 1 >= max_retries:
                raise
            if e.code != HTTPStatus.TOO_MANY_REQUESTS:
                raise
            retry_after = e.headers.get("Retry-After")
            if retry_after:
                wait = int(retry_after)
            else:
                wait = __get_backoff_time(attempt)
            print(f"HTTP status 429 received. Retrying in {wait:.2f} seconds...")
            time.sleep(wait)
        except URLError as e:
            if attempt + 1 >= max_retries:
                raise
            print(f"Network error: {e}. Retrying...")
            time.sleep(__get_backoff_time(attempt))
    raise AlteredAPIError(f"Failed to fetch URL: {url}")


def __get_backoff_time(times):
    return (2**times) + random.uniform(0, 1)


def get_altered_api_locale(language_code):
    return (
        LOCALE_IRREGULAR_CODES[language_code]
        if language_code in LOCALE_IRREGULAR_CODES
        else f"{language_code}-{language_code}"
    )
