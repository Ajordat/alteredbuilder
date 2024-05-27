from django import template
from django.urls import translate_url

register = template.Library()


@register.simple_tag(takes_context=True)
def change_lang(context, lang: str, *args, **kwargs):
    path = context["request"].path

    return translate_url(path, lang)
