from django import template
from django.contrib.auth.models import User

from decks.models import Card


register = template.Library()


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
            return "table-light"
        case "rare":
            return "table-primary"
        case "unique":
            return "table-danger"
        case _:
            return ""


@register.simple_tag
def get_main_cost(card: Card) -> int:
    """Receive a Card object and return its hand cost.

    Args:
        card (Card): Card to retrieve the hand cost from.

    Returns:
        int: The Card's hand cost.
    """
    return getattr(card, card.type).main_cost


@register.simple_tag
def get_recall_cost(card: Card) -> int:
    """Receive a Card object and return its reserve cost.

    Args:
        card (Card): Card to retrieve the reserve cost from.

    Returns:
        int: The Card's reserve cost.
    """
    return getattr(card, card.type).recall_cost


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
        "legality",
        "other",
    ]
    args = [
        f"{key}={value}" for key, value in get_params.items() if key in allowed_params
    ] + [f"{key}={value}" for key, value in kwargs.items()]
    return "&".join([arg for arg in args if arg])


@register.filter
def params_to_filter_tag(get_params: dict) -> list[(str, str)]:
    """Receives the parameters of a GET request and transforms them into a list of
    tuples of key-values.

    Returns:
        list[(str, str)]: A list of tuple elements with the key-values of the GET
        params.
    """
    allowed_params = ["faction", "rarity", "type", "query", "legality", "other"]
    tags = []
    for param in get_params:
        if param in allowed_params:
            try:
                if param == "faction":
                    tags += [
                        (param.title(), Card.Faction(value).label.title())
                        for value in get_params[param].split(",")
                    ]
                elif param == "rarity":
                    tags += [
                        (param.title(), Card.Rarity(value).label.title())
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
def has_group(user: User, group_name: str) -> bool:
    """Receives a User and the name of a group and returns if the User is part of a
    Group with that name.

    Args:
        user (User): User to check.
        group_name (str): Group name.

    Returns:
        bool: If the User is part of a Group with that name.
    """
    return user.groups.filter(name=group_name).exists()