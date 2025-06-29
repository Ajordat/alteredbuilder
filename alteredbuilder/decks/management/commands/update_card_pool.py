from functools import lru_cache
import math
from typing import Any

from django.conf import settings
from django.core.management.base import CommandError
from django.utils.translation import activate

from config.commands import BaseCommand
from config.utils import (
    altered_api_paginator,
    fetch_with_backoff,
    get_altered_api_locale,
    get_user_agent,
)
from decks.exceptions import IgnoreCardType
from decks.models import Card, Set, Subtype


# Altered's API endpoint
CARDS_API_ENDPOINT = "/cards"
# If True, retrieve the unique cards
UPDATE_UNIQUES = False
QUERY_SET = ["ALIZE"]
# The API currently returns a private image link for unique cards in these languages
IMAGE_ERROR_LOCALES = ["es", "it", "de"]
HEADERS = {"User-Agent": get_user_agent("CardImporter")}
if QUERY_SET:
    SET_CACHE = [Set.objects.get(code=card_set) for card_set in QUERY_SET]
else:
    SET_CACHE = [card_set for card_set in Set.objects.all()]


class SubTypeCache:

    def __init__(self):
        self.cache = {}

    def add_subtype(self, reference: str, subtype: str) -> None:
        if "_U_" in reference:
            return
        family_id = self._get_family_id(reference)
        if family_id not in self.cache:
            self.cache[family_id] = subtype

    def get_subtype(self, reference: str) -> str | None:
        return self.cache.get(self._get_family_id(reference), None)

    def _get_family_id(self, reference: str):
        # Remove the rarity from the reference to create the family id
        return reference.rsplit("_", 1)[0]

    def clear(self):
        self.cache = {}


class Command(BaseCommand):
    help = "Updates the card pool by adding the latest cards"
    version = "1.0.0"

    def __init__(self, **kwargs):
        super().__init__(kwargs)
        self.subtypes = SubTypeCache()
        self.language_code = None

    def handle(self, *args: Any, **options: Any) -> None:
        """The command's entrypoint. Queries the API for each language."""

        for language, _ in settings.LANGUAGES:
            self.language_code = language
            activate(self.language_code)
            self.query_page()
            self.subtypes.clear()

    def query_page(self) -> None:
        """Query Altered's API to retrieve the card information.

        Raises:
            CommandError: If the API returns a response in a different format.
        """

        locale = get_altered_api_locale(self.language_code)

        params = []
        if UPDATE_UNIQUES:
            params.append(("rarity[]", "UNIQUE"))
        if len(QUERY_SET) > 0:
            params.extend([("cardSet[]", card_set) for card_set in QUERY_SET])

        for card in altered_api_paginator(
            CARDS_API_ENDPOINT,
            user_agent_task="CardImporter",
            params=params,
            locale=locale,
        ):

            # Iterate each card retrieved
            try:
                card_dict = self.extract_card(card)
            except IgnoreCardType:
                continue
            except KeyError:
                self.stderr.write(card)
                raise CommandError("Invalid card format encountered")

            try:
                # Cast RAW values into the rightful Enum/class/Model
                self.convert_choices(card_dict)
            except ValueError:
                continue

            if (
                card_dict["rarity"] == Card.Rarity.UNIQUE
                and self.language_code in IMAGE_ERROR_LOCALES
            ):
                # If it's a unique card and one of the failing languages,
                # skip the image
                card_dict["image_url"] = None

            try:
                # Attempt to retrieve the Card using the reference
                card_obj = Card.objects.get(reference=card_dict["reference"])
            except Card.DoesNotExist:
                # If it doesn't exist, create the card
                self.create_card(card_dict)
            else:
                # If the card exists, update it
                self.update_card(card_dict, card_obj)

    def extract_card(self, card: dict) -> dict:
        """Recieve the API response and extract the relevant values into a dictionary.

        Args:
            card (dict): The object returned by the API.

        Raises:
            IgnoreCardType: If it's a type of card that won't be added into the db.

        Returns:
            dict: The Card converted into a dictionary.
        """
        card_dict = {
            "reference": card["reference"],
            "name": card["name"],
            "faction": card["mainFaction"]["reference"],
            "type": card["cardType"]["reference"],
            "rarity": card["rarity"]["reference"],
            "image_url": card["imagePath"],
        }
        if "cardSubTypes" in card:
            card_dict["subtypes"] = [
                (subtype["reference"], subtype["name"])
                for subtype in card["cardSubTypes"]
            ]

        main_effect, echo_effect = self.fetch_effects(card_dict["reference"])

        if main_effect:
            card_dict["main_effect"] = main_effect

        if card_dict["type"] in ["TOKEN", "TOKEN_MANA", "FOILER"]:
            # Stop the parsing if the Card is one of these
            raise IgnoreCardType()

        if card_dict["type"] == "HERO":
            try:
                card_dict.update(
                    {
                        "reserve_count": card["elements"]["RESERVE"],
                        "permanent_count": card["elements"]["PERMANENT"],
                    }
                )
            except KeyError:
                card_dict.update({"reserve_count": 2, "permanent_count": 2})

        else:
            if card_dict["type"] == "TOKEN":
                card_dict.update({"main_cost": 0, "recall_cost": 0})
            else:
                card_dict.update(
                    {
                        "main_cost": int(card["elements"]["MAIN_COST"].strip("#")),
                        "recall_cost": int(card["elements"]["RECALL_COST"].strip("#")),
                    }
                )

            if echo_effect:
                card_dict["echo_effect"] = echo_effect

            if card_dict["type"] == "CHARACTER":
                card_dict.update(
                    {
                        "forest_power": int(
                            card["elements"]["FOREST_POWER"].strip("#")
                        ),
                        "mountain_power": int(
                            card["elements"]["MOUNTAIN_POWER"].strip("#")
                        ),
                        "ocean_power": int(card["elements"]["OCEAN_POWER"].strip("#")),
                    }
                )
        return card_dict

    def convert_choices(self, card_dict: dict) -> None:
        """Convert certain string values into the relevant Enum. It also retrieves the
        Set object of the Card.

        Args:
            card_dict (dict): The Card dict that needs to have its values cast.
        """
        try:
            card_dict["faction"] = Card.Faction(card_dict["faction"])
            card_dict["type"] = (
                getattr(Card.Type, card_dict["type"])
                if card_dict["type"] != "PERMANENT"
                else Card.Type.LANDMARK_PERMANENT
            )
            card_dict["rarity"] = getattr(Card.Rarity, card_dict["rarity"])
        except Exception as e:
            print(card_dict)
            raise e

        reference = card_dict["reference"]
        for card_set in SET_CACHE:
            if card_set.reference_code in reference:
                card_dict["set"] = card_set
                break

        card_dict["is_promo"] = "_P_" in reference
        card_dict["is_alt_art"] = "_A_" in reference

    def create_card(self, card_dict: dict) -> None:
        """Receive a card dict and store it as a Card object into the db.

        Args:
            card_dict (dict): The card dict.
        """
        try:
            subtypes = card_dict.pop("subtypes", False)
            card = Card.objects.create_card(**card_dict)

            self.link_subtypes(card, subtypes)

            self.stdout.write(f"card created: {card}")
        except KeyError:
            pass

    def update_card(self, card_dict: dict, card_obj: Card) -> None:
        """Get the card dict fields and update the Card object with those values.

        Args:
            card_dict (dict): The card extracted from the API.
            card_obj (Card): The Card object on the database.
        """

        card_fields = Card.get_base_fields()
        if "main_effect" in card_dict:
            card_fields += ["main_effect"]
        if "echo_effect" in card_dict:
            card_fields += ["echo_effect"]

        if card_obj.type == Card.Type.HERO:
            stats_fields = ["reserve_count", "permanent_count"]
        else:
            stats_fields = ["main_cost", "recall_cost"]
            if card_obj.type == Card.Type.CHARACTER:
                stats_fields += ["forest_power", "mountain_power", "ocean_power"]

        for field in card_fields:
            setattr(card_obj, field, card_dict[field])

        card_obj.stats = {field: card_dict[field] for field in stats_fields}

        card_obj.save()

        self.link_subtypes(card_obj, card_dict.get("subtypes", None))

        self.stdout.write(f"card updated: {card_obj}")

    def link_subtypes(self, card: Card, subtypes: list[str]) -> None:
        if not subtypes:
            reference = card.reference
            subtypes = self.subtypes.get_subtype(reference)
            if not subtypes:
                subtypes = self.fetch_subtypes(reference)
                self.subtypes.add_subtype(reference, subtypes)

        for subtype in subtypes:
            # Retrieve the Subtype and create a relationship with the Card
            # If it doesn't exist, create it
            st_reference, st_name = subtype
            try:
                st = Subtype.objects.get(reference=st_reference)
                st.name = st_name
                st.save()
            except Subtype.DoesNotExist:
                st = Subtype.objects.create(reference=st_reference, name=st_name)
            card.subtypes.add(st)

    def fetch_subtypes(self, reference: str) -> list[(str, str)]:

        data = self._fetch_details(reference, self.language_code)

        try:
            return [(st["reference"], st["name"]) for st in data["cardSubTypes"]]
        except KeyError:
            return []

    def fetch_effects(self, reference: str) -> tuple[str | None, str | None]:

        data: dict = self._fetch_details(reference, self.language_code)
        stats: dict = data.get("elements", {})
        return stats.get("MAIN_EFFECT"), stats.get("ECHO_EFFECT")

    @lru_cache(maxsize=16)
    def _fetch_details(self, reference: str, locale: str) -> dict:
        # Adding a cache to this call allows us to prevent repeated calls to the remote
        # API. This is very useful because each reference is extracted twice:
        #  1 - Extracting the card effects
        #  2 - Extracting the subtypes
        # However, we need to add the locale in the header because we want to get the
        # details in other languages as well. If we didn't, we'd be getting the same
        # language for all versions of each card.

        locale = get_altered_api_locale(self.language_code)
        HEADERS["Accept-Language"] = locale
        params = f"locale={locale}"

        # Query the API
        return fetch_with_backoff(
            f"{settings.ALTERED_API_BASE_URL}{CARDS_API_ENDPOINT}/{reference}?{params}",
            HEADERS,
        )
