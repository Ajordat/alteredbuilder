from django import template

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
    allowed_params = ["faction", "rarity", "type"]
    args = [
        f"{key}={value}" for key, value in get_params.items() if key in allowed_params
    ] + [f"{key}={value}" for key, value in kwargs.items()]
    return "&".join([arg for arg in args if arg])
