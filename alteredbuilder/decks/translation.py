from modeltranslation.translator import register, TranslationOptions

from decks.models import Card, Set, Subtype, Tag


@register(Set)
class SetTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(Card)
class CardTranslationOptions(TranslationOptions):
    fields = ("name", "image_url", "main_effect", "echo_effect")


@register(Subtype)
class SubtypeTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(Tag)
class TagTranslationOptions(TranslationOptions):
    fields = ("description",)
