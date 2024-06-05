from django import template
from django.template.defaultfilters import stringfilter

import markdown as md

register = template.Library()


@register.filter
@stringfilter
def markdown(value: str) -> str:
    """Receives a markdown-formatted string and returns it converted into HTML.

    Args:
        value (str): Markdown-formatted string.

    Returns:
        str: HTML code version of the received string.
    """
    return md.markdown(value, extensions=["markdown.extensions.fenced_code"])
