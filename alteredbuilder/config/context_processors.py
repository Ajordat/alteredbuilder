from django.conf import settings
from django.utils.timezone import datetime
import environ


def add_version(request):
    env = environ.Env(COMMIT_ID=(str, "XXXXXXX"))
    return {"version": settings.VERSION, "build": env("COMMIT_ID")}


def add_release_date(request):
    return {"release_date": datetime(2024, 9, 13)}
