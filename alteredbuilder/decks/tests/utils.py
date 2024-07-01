from collections.abc import Generator
from contextlib import contextmanager
import logging
from random import randint
from typing import Union

from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.test import TestCase
from django.urls import reverse

from decks.models import Card, CardInDeck, Character, Deck, Hero, Permanent, Spell


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


def generate_card(
    faction: Card.Faction, card_type: Card.Type, rarity: Card.Rarity
) -> Union[Hero, Character, Spell, Permanent]:
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


def create_cid(
    times: int,
    deck: Deck,
    quantity: int,
    faction: Card.Faction,
    type: Card.Type,
    rarity: Card.Rarity,
) -> None:
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


def get_detail_card_list(deck: Deck, card_type: Card.Type) -> list[int, Card]:
    """Return the quantity and model of cards of the Deck filtered by their type.

    Args:
        deck (Deck): The deck containing the cards.
        card_type (Card.Type): The type of card to filter.

    Returns:
        list[int, Card]: The list of cards with their amount.
    """
    return [
        (c.quantity, c.card)
        for c in deck.cardindeck_set.all()
        if c.card.type == card_type
    ]


class AjaxTestCase(TestCase):
    def assert_ajax_error(
        self, response: HttpResponse, status_code: int, error_message: str
    ):
        """Method to verify the integrity of an error message to an AJAX request.

        Args:
            response (HttpResponse): Response received from the server.
            status_code (int): Expected HTTP status code.
            error_message (str): Expected string response for the given error.
        """
        self.assertEqual(response.status_code, status_code)
        self.assertIn("error", response.json())
        self.assertEqual(response.json()["error"]["code"], status_code)
        self.assertEqual(response.json()["error"]["message"], error_message)


class BaseViewTestCase(TestCase):

    TEST_USER = "test_user"
    OTHER_TEST_USER = "other_test_user"
    PUBLIC_DECK_NAME = "test_public_deck"
    PRIVATE_DECK_NAME = "test_private_deck"

    @classmethod
    def setUpTestData(cls):
        """Create the database data for this test.

        Specifically, it creates:
        * 2 User
        * 1 Hero
        * 1 Character
        * 1 Spell
        * 1 Permanent
        * 4 Deck
        """
        hero = generate_card(Card.Faction.AXIOM, Card.Type.HERO, Card.Rarity.COMMON)
        character = generate_card(
            Card.Faction.AXIOM, Card.Type.CHARACTER, Card.Rarity.RARE
        )
        spell = generate_card(Card.Faction.AXIOM, Card.Type.SPELL, Card.Rarity.RARE)
        permanent = generate_card(
            Card.Faction.AXIOM, Card.Type.PERMANENT, Card.Rarity.RARE
        )

        cls.user = User.objects.create_user(username=cls.TEST_USER)
        cls.other_user = User.objects.create_user(username=cls.OTHER_TEST_USER)
        cls.create_decks_for_user(cls.user, hero, [character, spell, permanent])
        cls.create_decks_for_user(cls.other_user, hero, [character, spell, permanent])

    @classmethod
    def create_decks_for_user(cls, user: User, hero: Hero, cards: list[Card]):
        """Create a public and a private deck based on the received parameters.

        Args:
            user (User): The owner of the decks.
            hero (Hero): The Deck's Hero.
            cards (list[Card]): The Deck's cards.
        """
        public_deck = Deck.objects.create(
            owner=user, name=cls.PUBLIC_DECK_NAME, hero=hero, is_public=True
        )
        private_deck = Deck.objects.create(
            owner=user, name=cls.PRIVATE_DECK_NAME, hero=hero, is_public=False
        )
        for card in cards:
            CardInDeck.objects.create(deck=public_deck, card=card, quantity=2)
            CardInDeck.objects.create(deck=private_deck, card=card, quantity=2)


class BaseFormTestCase(TestCase):
    """Test case focusing on the Forms."""

    USER_NAME = "test_user"
    OTHER_USER = "other_test_user"
    DECK_NAME = "test deck"
    HERO_REFERENCE = "ALT_CORE_B_AX_01_C"
    CHARACTER_REFERENCE = "ALT_CORE_B_YZ_08_R2"

    @classmethod
    def setUpTestData(cls):
        """Create the database data for this test.

        Specifically, it creates:
        * 2 User
        * 1 Hero
        * 1 Character
        * 2 Deck
        """
        cls.user = User.objects.create_user(username=cls.USER_NAME)
        other_user = User.objects.create_user(username=cls.OTHER_USER)

        Hero.objects.create(
            reference=cls.HERO_REFERENCE,
            name="Sierra & Oddball",
            faction=Card.Faction.AXIOM,
            type=Card.Type.HERO,
            rarity=Card.Rarity.COMMON,
        )
        generate_card(Card.Faction.AXIOM, Card.Type.HERO, Card.Rarity.COMMON)
        Character.objects.create(
            reference=cls.CHARACTER_REFERENCE,
            name="Yzmir Stargazer",
            faction=Card.Faction.AXIOM,
            type=Card.Type.CHARACTER,
            rarity=Card.Rarity.RARE,
            main_cost=1,
            recall_cost=1,
            forest_power=1,
            mountain_power=2,
            ocean_power=1,
        )
        Deck.objects.create(owner=cls.user, name=cls.DECK_NAME)
        Deck.objects.create(owner=other_user, name=cls.DECK_NAME)
