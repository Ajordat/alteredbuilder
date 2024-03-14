from django.contrib import admin

from .models import CardInDeck, Character, Deck, Hero, Landmark, Spell


# Register your models here.
admin.site.register(Character)
admin.site.register(CardInDeck)
admin.site.register(Deck)
admin.site.register(Hero)
admin.site.register(Landmark)
admin.site.register(Spell)
