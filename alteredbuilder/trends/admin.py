from collections import OrderedDict
from datetime import timedelta
from typing import Any

from django import forms
from django.conf import settings
from django.contrib import admin
from django.db.models.query import QuerySet
from django.http import HttpRequest
from django.utils.timezone import localdate

from decks.models import Card
from trends.models import CardTrend, DeckTrend, FactionTrend, HeroTrend, UserTrend


class FilterHeroForm(forms.ModelForm):
    class Meta:
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super(FilterHeroForm, self).__init__(*args, **kwargs)
        if "hero" in self.fields:
            self.fields["hero"].queryset = Card.objects.filter(
                type=Card.Type.HERO, set__code="CORE"
            )


class TrendUtilities(admin.ModelAdmin):
    actions = ["move_trend"]
    form = FilterHeroForm

    def get_actions(self, request: HttpRequest) -> OrderedDict[Any, Any]:
        actions = super().get_actions(request)
        if not settings.DEBUG:
            del actions["move_trend"]
        return actions

    @admin.action(description="Move trend to current timestamps")
    def move_trend(self, request, queryset: QuerySet[Card]):
        yesterday = localdate() - timedelta(days=1)
        updated = queryset.update(date=yesterday)
        self.message_user(request, f"{updated} trends were moved to yesterday.")


@admin.register(FactionTrend)
class FactionTrendAdmin(TrendUtilities):
    list_display = ["date", "count", "faction"]
    list_filter = ["faction"]


@admin.register(HeroTrend)
class HeroTrendAdmin(TrendUtilities):
    list_display = ["date", "count", "hero"]


@admin.register(CardTrend)
class CardTrendAdmin(TrendUtilities):
    list_display = ["date", "ranking", "card", "faction", "hero"]
    search_fields = ["hero__name_en", "card__name_en"]
    list_filter = ["faction", "ranking"]


@admin.register(DeckTrend)
class DeckTrendAdmin(TrendUtilities):
    list_display = ["date", "ranking", "deck", "faction", "hero"]
    search_fields = ["hero__name_en", "deck__name"]
    list_filter = ["faction", "ranking"]


@admin.register(UserTrend)
class UserTrendAdmin(TrendUtilities):
    list_display = ["date", "count", "user"]
    search_fields = ["user"]
    list_filter = ["date"]
