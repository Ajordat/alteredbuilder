from modeltranslation.translator import register, TranslationOptions

from .models import Card, Character, Hero, Permanent, Spell


@register(Card)
class CardTranslationOptions(TranslationOptions):
    fields = ("name", "image_url", "main_effect_temp", "echo_effect_temp")


@register(Hero)
class HeroTranslationOptions(TranslationOptions):
    fields = ("main_effect",)


@register([Character, Spell, Permanent])
class PlayableCardTranslationOptions(TranslationOptions):
    fields = (
        "main_effect",
        "echo_effect",
    )
