from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from decks.models import Deck


class StaticViewSitemap(Sitemap):
    priority = 0.6
    changefreq = "weekly"
    # i18n = True

    def items(self):
        return [
            "about",
            "collaborators",
            "privacy-policy",
            "terms-and-conditions",
            "markdown",
        ]

    def location(self, item):
        return reverse(item)


class DailyLocalizedStaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = "daily"
    i18n = True

    def items(self):
        return ["home", "deck-list"]

    def location(self, item):
        return reverse(item)


class MonthlyLocalizedStaticViewSitemap(Sitemap):
    priority = 0.6
    changefreq = "monthly"
    i18n = True

    def items(self):
        return ["about", "cards"]

    def location(self, item):
        return reverse(item)


class DeckSitemap(Sitemap):
    priority = 0.7
    changefreq = "weekly"

    def items(self):
        return Deck.objects.filter(is_public=True).exclude(description="")

    def lastmod(self, obj):
        return obj.modified_at

    def location(self, item):
        return reverse("deck-detail", kwargs={"pk": item.pk})
