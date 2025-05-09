from typing import Any
from django import template

from decks.models import Card


register = template.Library()


# TODO: Separate common tags into their own templatetags file
@register.simple_tag
def dict_get(d: dict, key: Any, default: Any) -> Any:
    return d.get(key, default)


@register.simple_tag
def subtract(minuend: Any, subtrahend: Any) -> Any:
    return minuend - subtrahend


@register.simple_tag
def display_price(dividend: Any) -> Any:
    if not dividend:
        return "-"
    return dividend / 100


@register.simple_tag
def first_nonnull(*values):
    return next((v for v in values if v), "")


@register.simple_tag
def get_row_color_from_rarity(rarity: str) -> str:
    """Return the desired row color depending on a card's rarity.

    Args:
        rarity (str): The card's rarity.

    Returns:
        str: The rarity's row color.
    """
    match rarity:
        case "common":
            return "table-secondary"
        case "rare":
            return "table-primary"
        case "unique":
            return "table-danger"
        case _:
            return ""


@register.simple_tag
def inject_params(get_params: dict, **kwargs) -> str:
    """Receives the parameters of a GET request, filters them and injects the values
    received as named parameters and returns a string to be used as GET params.

    Args:
        get_params (dict): GET parameters.
        kwargs (dict): Key-value parameters to add to the query.

    Returns:
        str: New GET params query.
    """
    allowed_params = [
        "faction",
        "rarity",
        "type",
        "query",
        "order",
        "tag",
        "legality",
        "deck",
        "other",
        "set",
    ]
    args = [
        f"{key}={value}"
        for key, value in get_params.items()
        if key in allowed_params and key not in kwargs.keys()
    ] + [f"{key}={value}" for key, value in kwargs.items() if value]
    return "&".join([arg for arg in args if arg])


@register.filter
def deck_params_to_filter_tag(get_params: dict) -> list[(str, str)]:
    """Receives the parameters of a GET request and transforms them into a list of
    tuples of key-values.

    Returns:
        list[(str, str)]: A list of tuple elements with the key-values of the GET
        params.
    """
    allowed_params = ["faction", "legality", "tag", "other"]
    tags = []
    for param in get_params:
        if param in allowed_params:
            try:
                if param == "faction":
                    tags += [
                        (param.title(), Card.Faction(value).label.title())
                        for value in get_params[param].split(",")
                    ]
                else:
                    tags += [
                        (param.title(), value.title())
                        for value in get_params[param].split(",")
                    ]
            except ValueError:
                pass

    return tags


@register.filter
def card_params_to_filter_tag(get_params: dict) -> list[(str, str)]:
    """Receives the parameters of a GET request and transforms them into a list of
    tuples of key-values.

    Returns:
        list[(str, str)]: A list of tuple elements with the key-values of the GET
        params.
    """
    allowed_params = ["faction", "rarity", "type"]
    tags = []
    for param in get_params:
        if param in allowed_params:
            try:
                if param == "faction":
                    tags += [
                        (param.title(), ": ", Card.Faction(value).label.title())
                        for value in get_params[param].split(",")
                    ]
                elif param == "rarity":
                    tags += [
                        (param.title(), ": ", Card.Rarity(value).label.title())
                        for value in get_params[param].split(",")
                    ]
                else:
                    tags += [
                        (param.title(), ": ", value.title())
                        for value in get_params[param].split(",")
                    ]
            except ValueError:
                continue

    return tags


@register.filter
def safe_username(username: str) -> str:
    return username.partition("@")[0]


@register.simple_tag
def cdn_image_url(image_url: str):

    return (
        f"https://www.altered.gg/cdn-cgi/image/format=auto,height=500,q=100,sharpen=1/{image_url}"
        if image_url
        else ""
    )
