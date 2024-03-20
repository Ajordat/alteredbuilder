from django.contrib import admin

from .models import CardInDeck, Character, Deck, Hero, Permanent, Spell


# Register your models here.
admin.site.register(Character)
admin.site.register(CardInDeck)
admin.site.register(Deck)
admin.site.register(Hero)
admin.site.register(Permanent)
admin.site.register(Spell)
