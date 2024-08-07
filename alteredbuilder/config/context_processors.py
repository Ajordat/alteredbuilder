from django.conf import settings
import environ


def add_version(request):
    env = environ.Env(COMMIT_ID=(str, "XXXXXXX"))
    return {"version": settings.VERSION, "build": env("COMMIT_ID")}
