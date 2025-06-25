from abc import ABC
from collections import defaultdict
from enum import StrEnum

from django.db import migrations
from django.utils.translation import gettext_lazy as _


class GameMode(ABC):
    """Base class for all the game modes of the game.

    It contains the metrics that can be checked, the possible error codes and enforces
    a validation method.
    """

    MIN_FACTION_COUNT = None
    MAX_FACTION_COUNT = None
    MIN_TOTAL_COUNT = None
    MAX_RARE_COUNT = None
    MAX_UNIQUE_COUNT = None
    ENFORCE_INDIVIDUAL_UNIQUES = True
    MAX_SAME_FAMILY_CARD_COUNT = None
    IS_HERO_MANDATORY = None

    @classmethod
    def validate(cls, **kwargs) -> list:
        """Validate if the received parameters comply with this game mode's rules and
        returns a list with the error codes (`GameMode.ErrorCode`) of the noticed
        failures.

        Returns:
            list[GameMode.ErrorCode]: List of failed rules to be considered a valid
                                      deck for the format.
        """
        error_list = []

        if cls.MIN_FACTION_COUNT and (kwargs["faction_count"] < cls.MIN_FACTION_COUNT):
            error_list.append(cls.ErrorCode.ERR_MISSING_FACTION_COUNT)
        if cls.MAX_FACTION_COUNT and (kwargs["faction_count"] > cls.MAX_FACTION_COUNT):
            error_list.append(cls.ErrorCode.ERR_EXCEED_FACTION_COUNT)
        if cls.MIN_TOTAL_COUNT and (kwargs["total_count"] < cls.MIN_TOTAL_COUNT):
            error_list.append(cls.ErrorCode.ERR_NOT_ENOUGH_CARD_COUNT)
        if cls.MAX_RARE_COUNT and (kwargs["rare_count"] > cls.MAX_RARE_COUNT):
            error_list.append(cls.ErrorCode.ERR_EXCEED_RARE_COUNT)
        if cls.MAX_UNIQUE_COUNT and (kwargs["unique_count"] > cls.MAX_UNIQUE_COUNT):
            error_list.append(cls.ErrorCode.ERR_EXCEED_UNIQUE_COUNT)
        if cls.ENFORCE_INDIVIDUAL_UNIQUES and kwargs["repeats_same_unique"]:
            error_list.append(cls.ErrorCode.ERR_UNIQUE_IS_REPEATED)
        if cls.MAX_SAME_FAMILY_CARD_COUNT and (
            max(kwargs["family_count"].values(), default=0)
            > cls.MAX_SAME_FAMILY_CARD_COUNT
        ):
            error_list.append(cls.ErrorCode.ERR_EXCEED_SAME_FAMILY_COUNT)
        if cls.IS_HERO_MANDATORY and not kwargs["has_hero"]:
            error_list.append(cls.ErrorCode.ERR_MISSING_HERO)

        return error_list

    class ErrorCode(StrEnum):
        # Does not reach the minimum faction count
        ERR_MISSING_FACTION_COUNT = "ERR_MISSING_FACTION_COUNT"
        # Exceeds maximum faction count
        ERR_EXCEED_FACTION_COUNT = "ERR_EXCEED_FACTION_COUNT"
        # Does not reach minimum card count
        ERR_NOT_ENOUGH_CARD_COUNT = "ERR_NOT_ENOUGH_CARD_COUNT"
        # Exceeds maximum rare card count
        ERR_EXCEED_RARE_COUNT = "ERR_EXCEED_RARE_COUNT"
        # Exceeds maximum unique card count
        ERR_EXCEED_UNIQUE_COUNT = "ERR_EXCEED_UNIQUE_COUNT"
        # There are multiple copies of a single unique
        ERR_UNIQUE_IS_REPEATED = "ERR_UNIQUE_IS_REPEATED"
        # Exceeds maximum card count of same family
        ERR_EXCEED_SAME_FAMILY_COUNT = "ERR_EXCEED_SAME_FAMILY_COUNT"
        # No hero present in deck
        ERR_MISSING_HERO = "ERR_MISSING_HERO"

        def to_user(self, gm) -> str:
            """Build an error message including the GameMode's relevant metrics.

            Args:
                gm (GameMode): GameMode that failed on the current error.

            Returns:
                str: User-friendly error message.
            """
            match self.value:
                case GameMode.ErrorCode.ERR_EXCEED_FACTION_COUNT:
                    return _("Exceeds maximum faction count (%(count)s)") % {
                        "count": gm.MAX_FACTION_COUNT
                    }
                case GameMode.ErrorCode.ERR_NOT_ENOUGH_CARD_COUNT:
                    return _("Does not have enough cards (%(count)s)") % {
                        "count": gm.MIN_TOTAL_COUNT
                    }
                case GameMode.ErrorCode.ERR_EXCEED_RARE_COUNT:
                    return _("Exceeds the maximum RARE card count (%(count)s)") % {
                        "count": gm.MAX_RARE_COUNT
                    }
                case GameMode.ErrorCode.ERR_EXCEED_UNIQUE_COUNT:
                    return _("Exceeds the maximum UNIQUE card count (%(count)s)") % {
                        "count": gm.MAX_UNIQUE_COUNT
                    }
                case GameMode.ErrorCode.ERR_UNIQUE_IS_REPEATED:
                    return _("There's more than a single copy of a UNIQUE card")
                case GameMode.ErrorCode.ERR_EXCEED_SAME_FAMILY_COUNT:
                    return _(
                        "Exceeds the maximum card count for any given family (%(count)s)"
                    ) % {"count": gm.MAX_SAME_FAMILY_CARD_COUNT}
                case GameMode.ErrorCode.ERR_MISSING_HERO:
                    return _("Missing hero")
                case GameMode.ErrorCode.ERR_MISSING_FACTION_COUNT:
                    return _("Does not reach the minimum faction count (%(count)s)") % {
                        "count": gm.MIN_FACTION_COUNT
                    }

        @classmethod
        def from_list_to_user(cls, error_list: list[str], game_mode) -> list[str]:
            """Receives a list of errors and the relevant GameMode and returns a list
            with the errors user-friendly messages.

            Args:
                error_list (list[str]): List of the error codes string value.
                game_mode (GameMode): GameMode of the errors.

            Returns:
                list[str]: User-friendly string representation of the error codes.
            """
            return [cls(error).to_user(game_mode) for error in error_list]


class StandardGameMode(GameMode):
    """Class to represent the Standard game mode."""

    MAX_FACTION_COUNT = 1
    MIN_TOTAL_COUNT = 39
    MAX_RARE_COUNT = 15
    MAX_UNIQUE_COUNT = 3
    MAX_SAME_FAMILY_CARD_COUNT = 3
    IS_HERO_MANDATORY = True


class Doubles(StandardGameMode):
    """Class to represent the Doubles game mode."""

    MIN_FACTION_COUNT = 2
    MAX_FACTION_COUNT = 2


def update_deck_legality(deck) -> None:
    """Receives a Deck object, extracts all the relevant metrics, evaluates the Deck's
    legality on the Exalts Championship game mode and updates the model.

    Args:
        deck (Deck): Deck to evaluate and update
    """

    total_count = 0
    rare_count = 0
    unique_count = 0
    repeats_same_unique = False
    factions = [deck.hero.faction] if deck.hero else []
    family_count = defaultdict(int)

    decklist = deck.cardindeck_set.select_related("card").all()

    for cid in decklist:
        total_count += cid.quantity
        if cid.card.rarity == "R":
            rare_count += cid.quantity
        elif cid.card.rarity == "U":
            unique_count += cid.quantity
            if cid.quantity > 1:
                repeats_same_unique = True
        if cid.card.faction not in factions:
            factions.append(cid.card.faction)
        family_key = "_".join(cid.card.reference.split("_")[3:5])
        family_count[family_key] += cid.quantity

    data = {
        "faction_count": len(factions),
        "total_count": total_count,
        "rare_count": rare_count,
        "unique_count": unique_count,
        "family_count": family_count,
        "has_hero": bool(deck.hero),
        "repeats_same_unique": repeats_same_unique,
    }

    has_errors = Doubles.validate(**data)
    deck.is_doubles_legal = not has_errors


def init_models(apps):
    global Deck, Card
    Deck = apps.get_model("decks", "Deck")
    Card = apps.get_model("decks", "Card")


def force_update_legality(apps, schema_editor):
    init_models(apps)
    decks = Deck.objects.all()
    decks_chunk = []
    for deck in decks:
        update_deck_legality(deck)
        decks_chunk.append(deck)
        if len(decks_chunk) >= 1000:
            Deck.objects.bulk_update(decks_chunk, ["is_doubles_legal"])
            decks_chunk = []

    Deck.objects.bulk_update(decks_chunk, ["is_doubles_legal"])


def empty_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("decks", "0068_deck_is_doubles_legal"),
    ]

    operations = [
        migrations.RunPython(force_update_legality, reverse_code=empty_reverse)
    ]
