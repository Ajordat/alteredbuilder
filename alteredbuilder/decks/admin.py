from django.contrib import admin

from .models import CardInDeck, Character, Deck, Hero, Permanent, Spell


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
