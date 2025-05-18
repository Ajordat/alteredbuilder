import json
import math
from typing import Any, Generator
from urllib.request import Request, urlopen
from django.conf import settings


def get_user_agent(task: str) -> str:
    return settings.USER_AGENT_BASE.format(task)


def altered_api_paginator(
    endpoint: str,
    user_agent_task,
    params: dict = None,
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
            query_params += "&" + "&".join([f"{k}={v}" for k, v in params.items()])

        # Query the API
        with urlopen(Request(url + query_params, headers=headers)) as response:
            page = response.read()
            data = json.loads(page.decode("utf8"))

        total_items = min(data["hydra:totalItems"], total_items)
        page_count = min(
            math.ceil(total_items / settings.ALTERED_API_ITEMS_PER_PAGE), page_count
        )

        for item in data["hydra:member"]:
            yield item

        page_index += 1
