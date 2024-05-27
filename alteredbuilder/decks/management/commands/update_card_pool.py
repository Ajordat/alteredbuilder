import json
import math
from typing import Any
from urllib import request

from decks.models import Card

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import activate


# API_URL = "https://api.altered.gg/cards?rarity[]=UNIQUE"
API_URL = "https://api.altered.gg/cards"
ITEMS_PER_PAGE = 36
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Origin": "https://www.altered.gg",
}


class Command(BaseCommand):
    help = "Updates the card pool by adding the latest cards"

    def handle(self, *args: Any, **options: Any) -> str | None:

        for language, _ in settings.LANGUAGES:
            activate(language)
            self.query_page(language)
    
    def query_page(self, language_code):

        headers["Accept-Language"] = f"{language_code}-{language_code}"
        page_index = 1
        page_count = math.inf
        total_items = math.inf

        while page_index <= page_count:
            params = f"?page={page_index}&itemsPerPage={ITEMS_PER_PAGE}"
            req = request.Request(API_URL + params, headers=headers)
            with request.urlopen(req) as response:
                page = response.read()
                data = json.loads(page.decode("utf8"))

            total_items = min(data["hydra:totalItems"], total_items)
            page_count = min(math.ceil(total_items / ITEMS_PER_PAGE), page_count)

            for card in data["hydra:member"]:
                try:
                    card_dict = self.extract_card(card)
                except KeyError:
                    self.stderr.write(card)
                    raise CommandError("Invalid card format encountered")

                self.convert_choices(card_dict)
                try:
                    card_obj = Card.objects.get(reference=card_dict["reference"])
                except Card.DoesNotExist:
                    self.create_card(card_dict)
                else:
                    self.update_card(card_dict, card_obj)

            page_index += 1

    def extract_card(self, card):
        card_object = {
            "reference": card["reference"],
            "name": card["name"],
            "faction": card["mainFaction"]["reference"],
            "type": card["cardType"]["reference"],
            "rarity": card["rarity"]["reference"],
            "image_url": card["imagePath"],
        }
        if "MAIN_EFFECT" in card["elements"]:
            card_object["main_effect"] = card["elements"]["MAIN_EFFECT"]

        if card_object["type"] == "HERO":
            try:
                card_object.update(
                    {
                        "reserve_count": card["elements"]["RESERVE"],
                        "permanent_count": card["elements"]["PERMANENT"],
                    }
                )
            except KeyError:
                card_object.update({"reserve_count": 2, "permanent_count": 2})

        else:
            if card_object["type"] == "TOKEN":
                card_object.update({"main_cost": 0, "recall_cost": 0})
            else:
                card_object.update(
                    {
                        "main_cost": card["elements"]["MAIN_COST"],
                        "recall_cost": card["elements"]["RECALL_COST"],
                    }
                )

            if "ECHO_EFFECT" in card["elements"]:
                card_object["echo_effect"] = card["elements"]["ECHO_EFFECT"]
            if card_object["type"] == "CHARACTER":
                card_object.update(
                    {
                        "forest_power": card["elements"]["FOREST_POWER"],
                        "mountain_power": card["elements"]["MOUNTAIN_POWER"],
                        "ocean_power": card["elements"]["OCEAN_POWER"],
                    }
                )
        return card_object

    def convert_choices(self, card_object):
        card_object["faction"] = Card.Faction(card_object["faction"])
        card_object["type"] = getattr(Card.Type, card_object["type"])
        card_object["rarity"] = getattr(Card.Rarity, card_object["rarity"])

    def create_card(self, card_dict):
        try:
            if card_dict["type"] != Card.Type.TOKEN:
                self.stdout.write(f"{card_dict}")
            card = Card.Type.to_class(card_dict["type"]).objects.create(**card_dict)
            self.stdout.write(f"card created: {card}")
        except KeyError:
            pass

    def update_card(self, card_dict: dict, card_obj: Card):
        if card_dict["image_url"] == card_obj.image_url:
            # If the image hasn't changed, we assume the other attributes haven't changed
            return
        print(f"card_obj: {card_obj}")
        print(f"card_dict: {card_dict}")

        shared_fields = ["name", "faction", "image_url"]
        specific_fields = ["main_effect"]
        type_name = str(card_obj.type)

        if card_obj.type == Card.Type.HERO:
            specific_fields += ["reserve_count", "permanent_count"]
        else:
            specific_fields += ["main_cost", "recall_cost", "echo_effect"]
            if card_obj.type == Card.Type.CHARACTER:
                specific_fields += ["forest_power", "mountain_power", "ocean_power"]

        for field in shared_fields:
            setattr(card_obj, field, card_dict[field])

        for field in specific_fields:
            try:
                setattr(getattr(card_obj, type_name), field, card_dict[field])
            except KeyError:
                pass
        card_obj.save()
        getattr(card_obj, type_name).save()
