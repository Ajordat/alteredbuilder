from django.test import TestCase

from decks.models import Card
from decks.templatetags.markdown_extras import markdown

from .utils import generate_card


class MarkdownTestCase(TestCase):
    """Test case focusing on the markdown filter."""

    ALT_ICON_FORMAT = '<span class="altered-{}"></span>'
    ALT_CARD_REFERENCE_FORMAT = '<a class="card-hover" data-image-url="{url}" href="https://www.altered.gg/cards/{reference}" target="_blank">{name}<link href="{url}" rel="prefetch" /></a>'

    MD_IMAGE_FORMAT = '<img alt="{alt}" src="{url}" />'
    MD_ANCHOR_FORMAT = '<a href="{url}">{alt}</a>'

    IMAGE_URL = "https://example.com/card.png"

    def assert_icon(self, key):
        html_format = self.ALT_ICON_FORMAT.format(key)
        result = markdown(f"[[{key}]]")
        self.assertInHTML(html_format, result)

    def test_mana_icons(self):

        self.assert_icon("x")
        for mana_value in range(1, 10):
            self.assert_icon(mana_value)

    def test_region_icons(self):
        icon_keys = ["forest", "mountain", "water"]

        for key in icon_keys:
            self.assert_icon(key)

    def test_trigger_icons(self):
        icon_keys = ["etb", "hand", "reserve"]

        for key in icon_keys:
            self.assert_icon(key)

    def test_activate_icons(self):
        icon_keys = ["discard", "exhaust"]

        for key in icon_keys:
            self.assert_icon(key)

    def test_card_reference(self):
        card = generate_card(Card.Faction.AXIOM, Card.Type.CHARACTER, Card.Rarity.RARE)
        card.image_url = self.IMAGE_URL
        card.save()

        result = markdown(f"[[{card.reference}]]")
        html_format = self.ALT_CARD_REFERENCE_FORMAT.format(
            url=card.image_url, reference=card.reference, name=card.name
        )
        self.assertInHTML(html_format, result)

    def test_unknown_key(self):
        text = "[[unknown]]"
        result = markdown(text)
        self.assertInHTML(text, result)

    def test_remove_images(self):
        alt_text = "alternative text"
        url = self.IMAGE_URL
        text = f"![{alt_text}]({url})"

        result = markdown(text)

        img_result = self.MD_IMAGE_FORMAT.format(alt=alt_text, url=url)
        anchor_result = self.MD_ANCHOR_FORMAT.format(alt=alt_text, url=url)
        self.assertNotIn(img_result, result)
        self.assertInHTML(anchor_result, result)
