from django import template

register = template.Library()


@register.simple_tag
def get_row_color_from_rarity(rarity):
    match rarity:
        case "common":
            return "table-light"
        case "rare":
            return "table-primary"
        case "unique":
            return "table-danger"
        case _:
            return ""
