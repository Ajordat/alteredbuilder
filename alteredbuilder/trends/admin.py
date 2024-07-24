from django.contrib import admin

from .models import FactionTrend, HeroTrend


@admin.register(FactionTrend)
class FactionTrendAdmin(admin.ModelAdmin):
    list_display = ["date", "faction"]


@admin.register(HeroTrend)
class HeroTrendAdmin(admin.ModelAdmin):
    list_display = ["date", "hero"]
