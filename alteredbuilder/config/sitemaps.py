from django.contrib.sitemaps import Sitemap
from django.core.paginator import Paginator
from django.urls import reverse

from decks.models import Deck


class StaticViewSitemap(Sitemap):
    priority = 0.6
    changefreq = "weekly"
    # i18n = True

    def items(self):
        return ["about", "collaborators", "privacy-policy", "terms-and-conditions", "markdown"]

    def location(self, item):
        return reverse(item)


class LocalizedStaticViewSitemap(Sitemap):
    priority = 1
    changefreq = "daily"
    i18n = True

    def items(self):
        return ["home", "about", "deck-list", "cards"]

    def location(self, item):
        return reverse(item)


class DeckSitemap(Sitemap):
    priority = 0.5
    changefreq = "weekly"
    # limit = 200

    def items(self):
        return Deck.objects.filter(is_public=True)

    def lastmod(self, obj):
        return obj.modified_at

    def location(self, item):
        return reverse("deck-detail", kwargs={"pk": item.pk})