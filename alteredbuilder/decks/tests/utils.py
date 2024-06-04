from collections.abc import Generator
from contextlib import contextmanager
import logging
from random import randint
from typing import Union

from django.conf import settings
from decks.models import Card, CardInDeck, Character, Deck, Hero, Permanent, Spell
from django.urls import reverse


def get_id() -> Generator[int, None, None]:
    """Return an ID that hasn't been returned so far.

    Yields:
        Generator[int, None, None]: ID returned.
    """
    _id = 1
    while True:
        yield _id
        _id += 1

get_id = get_id()


def generate_card(faction: Card.Faction, card_type: Card.Type, rarity: Card.Rarity) -> Union[Hero, Character, Spell, Permanent]:
    """Generate a new card from a Faction, Type and Rarity.

    Args:
        faction (Card.Faction): Faction of the card.
        card_type (Card.Type): Type of the card.
        rarity (Card.Rarity): Rarity of the card.

    Returns:
        Union[Hero, Character, Spell, Permanent]: Created card.
    """
    card_id = next(get_id)
    data = {
        "reference": f"ALT_CORE_B_{faction.value}_{card_id}_{rarity.value}",
        "name": f"{card_type.value} card {card_id}",
        "faction": faction,
        "type": card_type,
        "rarity": rarity,
    }
    cost = {
        "main_cost": randint(1, 10),
        "recall_cost": randint(1, 10),
    }
    match card_type:
        case Card.Type.HERO:
            card = Hero.objects.create(**data)
        case Card.Type.CHARACTER:
            card = Character.objects.create(
                **data,
                **cost,
                forest_power=randint(0, 10),
                mountain_power=randint(0, 10),
                ocean_power=randint(0, 10),
            )
        case Card.Type.SPELL:
            card = Spell.objects.create(**data, **cost)
        case Card.Type.PERMANENT:
            card = Permanent.objects.create(**data, **cost)

    return card


def create_cid(times: int, deck: Deck, quantity: int, faction: Card.Faction, type: Card.Type, rarity: Card.Rarity) -> None:
    """Function to create a Card and link it to the received Deck.
    
    Note that the `times` parameter indicates how many times this operation is done.
    That means that a single Card will be added `quantity` times to the Deck, and this
    operation will be repeated that many `times`.

    Args:
        times (int): How many times a Card model should be created with the received
        parameters.
        deck (Deck): The Deck to link the Cards to.
        quantity (int): How many of the same Card should be linked to the Deck.
        faction (Card.Faction): Faction of the Card to create.
        type (Card.Type): Type of the Card to create.
        rarity (Card.Rarity): Rarity of the Card to create.
    """
    for _ in range(times):
        CardInDeck.objects.create(
            deck=deck,
            quantity=quantity,
            card=generate_card(faction, type, rarity),
        )


def get_login_url(template: str, **kwargs) -> str:
    """Return the login URL with the received template as the `next` parameter.

    Args:
        template (str): Name of the URL to be added on the `next` parameter.

    Returns:
        str: The built login URL.
    """
    return f"{settings.LOGIN_URL}?next={reverse(template, kwargs=kwargs)}"


@contextmanager
def silence_logging():
    """Context manager to silence the logging for a given block. Useful to disable
    request's error messages logged into the console while testing failing requests.
    """
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)