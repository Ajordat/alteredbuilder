from django.contrib import admin
from django.utils.html import format_html

from decks.admin import HeroFilter
from recommender.models import Tournament, TournamentDeck, TrainedModel


@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ["remote_id", "name", "location", "date"]


@admin.register(TournamentDeck)
class TournamentDeckAdmin(admin.ModelAdmin):
    list_display = [
        "player_id",
        "tournament_name",
        "player",
        "placement",
        "hero",
        "deck_link",
    ]
    search_fields = ["id", "remote_id", "cards"]
    list_filter = ["hero__faction", HeroFilter]

    def tournament_name(self, deck: TournamentDeck):
        return deck.tournament.name

    tournament_name.short_description = "Tournament"
    tournament_name.admin_order_field = "tournament__date"

    def deck_link(self, deck: TournamentDeck):
        return format_html(
            '<a href="{}" target="_blank">🔗</a>', deck.get_absolute_url()
        )

    deck_link.short_description = "Link"


@admin.register(TrainedModel)
class TrainedModelAdmin(admin.ModelAdmin):
    list_display = ["faction", "active", "model", "period_start", "period_end"]
