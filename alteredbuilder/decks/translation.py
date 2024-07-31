from modeltranslation.translator import register, TranslationOptions

from .models import Card, Subtype


@register(Card)
class CardTranslationOptions(TranslationOptions):
    fields = ("name", "image_url", "main_effect", "echo_effect")


@register(Subtype)
class SubtypeTranslationOptions(TranslationOptions):
    fields = ("name",)
