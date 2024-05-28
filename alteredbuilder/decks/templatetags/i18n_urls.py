from django import template
from django.urls import translate_url

register = template.Library()


@register.simple_tag(takes_context=True)
def change_lang(context: dict, lang: str, *args, **kwargs) -> str:
    path = context["request"].path

    return translate_url(path, lang)
