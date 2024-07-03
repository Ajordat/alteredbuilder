# import re

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
    # print(value)
    # matches = re.finditer(r"(?:\[\[(?P<reference>.*?)\]\])", value)
    # print([x.group("reference") for x in matches])
    return md.markdown(value, extensions=["markdown.extensions.fenced_code", "markdown_mark"])
