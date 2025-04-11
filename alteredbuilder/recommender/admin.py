from django.contrib import admin

from recommender.models import Tournament, TournamentDeck, TrainedModel


@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ["remote_id", "name", "location", "date"]


@admin.register(TournamentDeck)
class TournamentDeckAdmin(admin.ModelAdmin):
    list_display = ["remote_id", "placement", "hero"]
    search_fields = ["id", "remote_id"]


@admin.register(TrainedModel)
class TrainedModelAdmin(admin.ModelAdmin):
    list_display = ["faction", "active", "model", "period_start", "period_end"]
