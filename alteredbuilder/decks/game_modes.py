from abc import ABC
from collections import defaultdict
from enum import StrEnum

from django.utils.translation import gettext_lazy as _

from decks.models import Deck, Card


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
    BANNED_FAMILY_CARDS = []

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
        if len(cls.BANNED_FAMILY_CARDS) > 0 and any(
            ban in kwargs["card_families"] for ban in cls.BANNED_FAMILY_CARDS
        ):
            error_list.append(cls.ErrorCode.ERR_CONTAINS_BANNED_CARD)

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
        # Contains a banned card
        ERR_CONTAINS_BANNED_CARD = "ERR_CONTAINS_BANNED_CARD"

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
                case GameMode.ErrorCode.ERR_CONTAINS_BANNED_CARD:
                    return _("Contains a banned card")

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
    BANNED_FAMILY_CARDS = [
        ("YZ_05_U", Card.Faction.AXIOM),
        ("YZ_05_U", Card.Faction.YZMIR),
        ("AX_16_U", Card.Faction.BRAVOS),
    ]


class Doubles(StandardGameMode):
    """Class to represent the Doubles game mode."""

    MIN_FACTION_COUNT = 2
    MAX_FACTION_COUNT = 2


class ExaltsChampionship(StandardGameMode):
    """Class to represent the Standard game mode."""

    MAX_RARE_COUNT = 18
    MAX_UNIQUE_COUNT = 0


class DraftGameMode(GameMode):
    """Class to represent the Draft game mode."""

    MAX_FACTION_COUNT = 3
    MIN_TOTAL_COUNT = 30

    @classmethod
    def validate(cls, **kwargs) -> list[GameMode.ErrorCode]:
        error_list = []

        if kwargs["faction_count"] > cls.MAX_FACTION_COUNT:
            error_list.append(cls.ErrorCode.ERR_EXCEED_FACTION_COUNT)
        if (kwargs["total_count"] + int(kwargs["has_hero"])) < cls.MIN_TOTAL_COUNT:
            error_list.append(cls.ErrorCode.ERR_NOT_ENOUGH_CARD_COUNT)
        if kwargs["repeats_same_unique"]:
            error_list.append(cls.ErrorCode.ERR_UNIQUE_IS_REPEATED)

        return error_list


def update_deck_legality(deck: Deck) -> None:
    """Receives a Deck object, extracts all the relevant metrics, evaluates the Deck's
    legality on Standard and Draft game modes and updates the model.

    Args:
        deck (Deck): Deck to evaluate and update
    """

    total_count = 0
    rare_count = 0
    unique_count = 0
    repeats_same_unique = False
    factions = [deck.hero.faction] if deck.hero else []
    family_count = defaultdict(int)
    card_families = []

    decklist = deck.cardindeck_set.select_related("card").all()

    for cid in decklist:
        total_count += cid.quantity
        if cid.card.rarity == Card.Rarity.RARE:
            rare_count += cid.quantity
        elif cid.card.rarity == Card.Rarity.UNIQUE:
            unique_count += cid.quantity
            if cid.quantity > 1:
                repeats_same_unique = True
        if cid.card.faction not in factions:
            factions.append(cid.card.faction)
        family_key = cid.card.get_family_code()
        family_count[family_key] += cid.quantity
        card_families.append((cid.card.get_family(), cid.card.faction))

    data = {
        "faction_count": len(factions),
        "total_count": total_count,
        "rare_count": rare_count,
        "unique_count": unique_count,
        "family_count": family_count,
        "has_hero": bool(deck.hero),
        "repeats_same_unique": repeats_same_unique,
        "card_families": card_families,
    }

    error_list = StandardGameMode.validate(**data)
    deck.is_standard_legal = not bool(error_list)
    deck.standard_legality_errors = error_list

    error_list = DraftGameMode.validate(**data)
    deck.is_draft_legal = not bool(error_list)
    deck.draft_legality_errors = error_list

    has_errors = ExaltsChampionship.validate(**data)
    deck.is_exalts_legal = not has_errors

    has_errors = Doubles.validate(**data)
    deck.is_doubles_legal = not has_errors
