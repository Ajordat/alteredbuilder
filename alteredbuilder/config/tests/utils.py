from contextlib import contextmanager
import logging

from django.conf import settings
from django.urls import reverse


def get_login_url(template: str = None, next: str = None, **kwargs) -> str:
    """Return the login URL with the received template as the `next` parameter.

    Args:
        template (str): Name of the URL to be added on the `next` parameter.

    Returns:
        str: The built login URL.
    """
    if next:
        return f"{settings.LOGIN_URL}?next={next}"
    return f"{settings.LOGIN_URL}?next={reverse(template, kwargs=kwargs)}"


@contextmanager
def silence_logging():
    """Context manager to silence the logging for a given block. Useful to disable
    request's error messages logged into the console while testing failing requests.
    """
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)
