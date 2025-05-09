from argparse import ArgumentParser
from typing import Any
from urllib.error import HTTPError

from django.conf import settings
from django.core.management.base import CommandError
from django.db import IntegrityError
from django.utils import timezone

from config.commands import BaseCommand
from config.utils import altered_api_paginator
from decks.deck_utils import family_code_from_reference
from decks.models import Card, CardPrice


# Altered's API endpoint
CARDS_API_ENDPOINT = "/cards/stats"
TODAY = timezone.now().date()
IGNORED_CARDS = [
    "AX_31",  # Brassbug
    "BR_31",  # Booda
    "OR_31",  # Soldier
    "OR_32",  # Soldier
    "YZ_31",  # Maw
    "YZ_47",  # Moth
    "NE_02",  # Dragon
]


class Command(BaseCommand):
    help = "Updates the card prices from the marketplace"
    version = "1.0.0"

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument(
            "--token",
            action="store",
            help="Auth token",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """The command's entrypoint"""

        auth_token = options["token"] or settings.BOT_AUTHORIZATION_TOKEN

        if not auth_token:
            raise CommandError(
                "Unable to retrieve data from the marketplace without an Authorization token"
            )

        try:
            for faction in Card.Faction:
                self.query_faction_marketplace(faction, auth_token)
        except HTTPError as e:
            raise CommandError("Failed to connect to the Altered API: " + str(e))

    def query_faction_marketplace(self, faction: str, auth_token: str):

        for card in altered_api_paginator(
            CARDS_API_ENDPOINT,
            params={"factions[]": faction},
            user_agent_task="MarketplaceImporter",
            auth_token=auth_token,
        ):
            reference = card["@id"].split("/")[-1]

            family_code = family_code_from_reference(reference)
            if family_code in IGNORED_CARDS:
                continue

            count = card.get("inSale", 0)
            price = card.get("lowerPrice")
            price = price * 100 if price else None

            try:
                CardPrice.objects.update_or_create(
                    card_id=reference,
                    date=TODAY,
                    defaults={"price": price, "count": count},
                )
            except IntegrityError:
                print(f"Failed to insert {reference}")
