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
