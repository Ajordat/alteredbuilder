from django.contrib import admin

from .models import (
    CardInDeck,
    Character,
    Deck,
    Hero,
    LovePoint,
    Permanent,
    PrivateLink,
    Spell,
)


# Register your models here.


@admin.register(Deck)
class DeckAdmin(admin.ModelAdmin):
    list_display = ["owner", "name", "is_public", "modified_at"]


@admin.register(Character, Hero, Permanent, Spell)
class CardAdmin(admin.ModelAdmin):
    list_display = ["reference", "name", "rarity", "faction"]


@admin.register(CardInDeck)
class CardInDeckAdmin(admin.ModelAdmin):
    list_display = ["deck", "card"]


@admin.register(LovePoint)
class LovePointAdmin(admin.ModelAdmin):
    list_display = ["user", "deck", "created_at"]


@admin.register(PrivateLink)
class PrivateLinkAdmin(admin.ModelAdmin):
    list_display = ["code", "deck", "last_accessed_at", "created_at"]
