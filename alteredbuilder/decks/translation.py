from modeltranslation.translator import register, TranslationOptions

from .models import Card, Subtype


@register(Card)
class CardTranslationOptions(TranslationOptions):
    fields = ("name", "image_url", "main_effect_temp", "echo_effect_temp")


@register(Subtype)
class SubtypeTranslationOptions(TranslationOptions):
    fields = ("name",)
