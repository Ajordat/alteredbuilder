from django.contrib import admin

from .models import CardTrend, FactionTrend, HeroTrend


@admin.register(FactionTrend)
class FactionTrendAdmin(admin.ModelAdmin):
    list_display = ["date", "count", "faction"]


@admin.register(HeroTrend)
class HeroTrendAdmin(admin.ModelAdmin):
    list_display = ["date", "count", "hero"]


@admin.register(CardTrend)
class CardTrendAdmin(admin.ModelAdmin):
    list_display = ["date", "ranking", "card", "faction", "hero"]
