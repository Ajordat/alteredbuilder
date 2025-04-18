from django.core.management.base import BaseCommand


class BaseCommand(BaseCommand):
    version = "0.0.1"
    suppressed_base_arguments = [
        "--verbosity",
        "--settings",
        "--pythonpath",
        "--no-color",
        "--force-color",
        "--skip-checks",
    ]

    def get_version(self):
        return self.version
