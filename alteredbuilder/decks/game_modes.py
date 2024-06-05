from abc import ABC, abstractmethod
from collections import defaultdict
from enum import StrEnum

from django.utils.translation import gettext_lazy as _

from .models import Deck, Card


class GameMode(ABC):
    """Base class for all the game modes of the game.

    It contains the metrics that can be checked, the possible error codes and enforces
    a validation method.
    """

    MAX_FACTION_COUNT = None
    MIN_TOTAL_COUNT = None
    MAX_RARE_COUNT = None
    MAX_UNIQUE_COUNT = None
    MAX_SAME_FAMILY_CARD_COUNT = None
    IS_HERO_MANDATORY = None

    @classmethod
    @abstractmethod
    def validate(cls, **kwargs) -> list:
        """Validate if the received parameters comply with this game mode's rules and
        returns a list with the error codes (`GameMode.ErrorCode`) of the noticed
        failures.

        Returns:
            list[GameMode.ErrorCode]: List of failed rules to be considered a valid
                                      deck for the format.
        """
        pass

    class ErrorCode(StrEnum):
        # Exceeds maximum faction count
        ERR_EXCEED_FACTION_COUNT = "ERR_EXCEED_FACTION_COUNT"
        # Does not reach minimum card count
        ERR_NOT_ENOUGH_CARD_COUNT = "ERR_NOT_ENOUGH_CARD_COUNT"
        # Exceeds maximum rare card count
        ERR_EXCEED_RARE_COUNT = "ERR_EXCEED_RARE_COUNT"
        # Exceeds maximum unique card count
        ERR_EXCEED_UNIQUE_COUNT = "ERR_EXCEED_UNIQUE_COUNT"
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
                case GameMode.ErrorCode.ERR_EXCEED_SAME_FAMILY_COUNT:
                    return _(
                        "Exceeds the maximum card count for any given family (%(count)s)"
                    ) % {"count": gm.MAX_SAME_FAMILY_CARD_COUNT}
                case GameMode.ErrorCode.ERR_MISSING_HERO:
                    return _("Missing hero")

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

    @classmethod
    def validate(cls, **kwargs) -> list[GameMode.ErrorCode]:
        error_list = []

        if kwargs["faction_count"] > cls.MAX_FACTION_COUNT:
            error_list.append(cls.ErrorCode.ERR_EXCEED_FACTION_COUNT)
        if kwargs["total_count"] < cls.MIN_TOTAL_COUNT:
            error_list.append(cls.ErrorCode.ERR_NOT_ENOUGH_CARD_COUNT)
        if kwargs["rare_count"] > cls.MAX_RARE_COUNT:
            error_list.append(cls.ErrorCode.ERR_EXCEED_RARE_COUNT)
        if kwargs["unique_count"] > cls.MAX_UNIQUE_COUNT:
            error_list.append(cls.ErrorCode.ERR_EXCEED_UNIQUE_COUNT)
        if (
            max(kwargs["family_count"].values(), default=0)
            > cls.MAX_SAME_FAMILY_CARD_COUNT
        ):
            error_list.append(cls.ErrorCode.ERR_EXCEED_SAME_FAMILY_COUNT)
        if not kwargs["has_hero"] and cls.IS_HERO_MANDATORY:
            error_list.append(cls.ErrorCode.ERR_MISSING_HERO)

        return error_list


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
    factions = [deck.hero.faction] if deck.hero else []
    family_count = defaultdict(int)

    decklist = (
        deck.cardindeck_set.select_related("card").order_by("card__reference").all()
    )

    for cid in decklist:
        total_count += cid.quantity
        if cid.card.rarity == Card.Rarity.RARE:
            rare_count += cid.quantity
        elif cid.card.rarity == Card.Rarity.UNIQUE:
            unique_count += cid.quantity
        if cid.card.faction not in factions:
            factions.append(cid.card.faction)
        family_key = "_".join(cid.card.reference.split("_")[:-1])
        family_count[family_key] += cid.quantity

    data = {
        "faction_count": len(factions),
        "total_count": total_count,
        "rare_count": rare_count,
        "unique_count": unique_count,
        "family_count": family_count,
        "has_hero": bool(deck.hero),
    }

    error_list = StandardGameMode.validate(**data)
    deck.is_standard_legal = not bool(error_list)
    deck.standard_legality_errors = error_list

    error_list = DraftGameMode.validate(**data)
    deck.is_draft_legal = not bool(error_list)
    deck.draft_legality_errors = error_list
