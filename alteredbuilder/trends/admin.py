from collections import OrderedDict
from datetime import timedelta
from typing import Any

from django.conf import settings
from django.contrib import admin
from django.http import HttpRequest
from django.utils.timezone import localdate

from trends.models import CardTrend, DeckTrend, FactionTrend, HeroTrend


class TrendUtilities:
    actions = ["move_trend"]

    def get_actions(self, request: HttpRequest) -> OrderedDict[Any, Any]:
        actions = super().get_actions(request)
        if not settings.DEBUG:
            del actions["move_trend"]
        return actions

    @admin.action(description="Move trend to current timestamps")
    def move_trend(self, request, queryset):
        yesterday = localdate() - timedelta(days=1)
        updated = queryset.update(date=yesterday)
        self.message_user(request, f"{updated} trends were moved to yesterday.")


@admin.register(FactionTrend)
class FactionTrendAdmin(TrendUtilities, admin.ModelAdmin):
    list_display = ["date", "count", "faction"]
    list_filter = ["faction"]


@admin.register(HeroTrend)
class HeroTrendAdmin(TrendUtilities, admin.ModelAdmin):
    list_display = ["date", "count", "hero"]


@admin.register(CardTrend)
class CardTrendAdmin(TrendUtilities, admin.ModelAdmin):
    list_display = ["date", "ranking", "card", "faction", "hero"]
    search_fields = ["hero__name_en", "card__name_en"]
    list_filter = ["faction", "ranking"]


@admin.register(DeckTrend)
class DeckTrendAdmin(TrendUtilities, admin.ModelAdmin):
    list_display = ["date", "ranking", "deck", "faction", "hero"]
    search_fields = ["hero__name_en", "deck__name"]
    list_filter = ["faction", "ranking"]
