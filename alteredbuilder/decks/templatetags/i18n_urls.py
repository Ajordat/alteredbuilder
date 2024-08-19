from django import template
from django.urls import translate_url


register = template.Library()


@register.simple_tag(takes_context=True)
def change_lang(context: dict, lang: str, *args, **kwargs) -> str:
    """Return the current URL translated to the specified language.

    Args:
        context (dict): Template context.
        lang (str): Target language.

    Returns:
        str: Current URL translated to the target language.
    """
    path = context["request"].get_full_path()

    return translate_url(path, lang)
