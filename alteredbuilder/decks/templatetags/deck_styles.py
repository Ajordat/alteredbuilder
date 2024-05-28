from django import template

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
def get_main_cost(card):
    return getattr(card, card.type).main_cost


@register.simple_tag
def get_recall_cost(card):
    return getattr(card, card.type).recall_cost


@register.simple_tag
def inject_params(get_params, **kwargs):
    allowed_params = ["faction", "rarity", "type", "query", "order"]
    args = [
        f"{key}={value}" for key, value in get_params.items() if key in allowed_params
    ] + [f"{key}={value}" for key, value in kwargs.items()]
    return "&".join([arg for arg in args if arg])


@register.filter
def params_to_filter_tag(get_params):
    allowed_params = ["faction", "rarity", "type", "query"]
    tags = []
    for param in get_params:
        if param in allowed_params:
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

    return tags
