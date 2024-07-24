from django.contrib import admin

from .models import FactionTrend


@admin.register(FactionTrend)
class FactionTrendAdmin(admin.ModelAdmin):
    list_display = ["date", "faction"]
