from re import Match
from xml.etree.ElementTree import Element
from django import template
from django.template.defaultfilters import stringfilter

import markdown as md
from markdown.extensions import Extension
from markdown.inlinepatterns import InlineProcessor

from decks.models import Card


ALTERED_API = "https://www.altered.gg/cards/"
REFERENCE_RE = r"\[\[(.*?)\]\]"
ICON_LIST = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "etb", "exhaust", "forest", "hand", "mountain", "reserve", "support", "water", "x"]


class InlineCardReferenceProcessor(InlineProcessor):
    def handleMatch(
        self, m: Match[str], data: str
    ) -> tuple[Element | str | None, int | None, int | None]:
        reference = m.group(1)
        if reference in ICON_LIST:
            element = Element("span")
            element.attrib["class"] = "altered-" + reference
        else:
            try:
                element = Element("a", href=ALTERED_API + reference, target="_blank")
                card = Card.objects.get(reference=reference)
                element.text = card.name
                element.attrib["class"] = "card-hover"
                element.attrib["data-image-url"] = card.image_url
                prefetch = Element("link", rel="prefetch", href=card.image_url)
                element.append(prefetch)
            except Card.DoesNotExist:
                element = None

        return element, m.start(0), m.end(0)


class AlteredCardsExtension(Extension):
    def extendMarkdown(self, md: md.Markdown) -> None:
        md.inlinePatterns.register(
            InlineCardReferenceProcessor(REFERENCE_RE, md),
            "inlinecardreferenceprocessor",
            30,
        )


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
    return md.markdown(value, extensions=["markdown_mark", AlteredCardsExtension()])
