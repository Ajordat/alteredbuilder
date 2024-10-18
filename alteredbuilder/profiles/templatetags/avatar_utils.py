from django import template
from django.templatetags.static import static


register = template.Library()


@register.filter
def to_avatar_url(avatar_name: str) -> str:
    return static("/img/avatars/" + avatar_name)
