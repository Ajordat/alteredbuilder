from . import __version__
import environ


def add_version(request):
    env = environ.Env(COMMIT_ID=(str, "XXXXXXX"))
    return {"version": __version__, "build": env("COMMIT_ID")}
