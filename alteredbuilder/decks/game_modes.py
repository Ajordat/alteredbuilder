from abc import ABC, abstractmethod
from collections import defaultdict
from enum import StrEnum

from .models import Deck, Card


class GameMode(ABC):
    MAX_FACTION_COUNT = None
    MIN_TOTAL_COUNT = None
    MAX_RARE_COUNT = None
    MAX_UNIQUE_COUNT = None
    MAX_SAME_FAMILY_CARD = None

    @classmethod
    @abstractmethod
    def validate(cls, **kwargs):
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

        def to_user(self, gm):
            match self.value:
                case GameMode.ErrorCode.ERR_EXCEED_FACTION_COUNT:
                    return f"Exceeds maximum faction count ({gm.MAX_FACTION_COUNT})"
                case GameMode.ErrorCode.ERR_NOT_ENOUGH_CARD_COUNT:
                    return f"Does not have enough cards ({gm.MIN_TOTAL_COUNT})"
                case GameMode.ErrorCode.ERR_EXCEED_RARE_COUNT:
                    return f"Exceeds the maximum RARE card count ({gm.MAX_RARE_COUNT})"
                case GameMode.ErrorCode.ERR_EXCEED_UNIQUE_COUNT:
                    return (
                        f"Exceeds the maximum UNIQUE card count ({gm.MAX_UNIQUE_COUNT})"
                    )
                case GameMode.ErrorCode.ERR_EXCEED_SAME_FAMILY_COUNT:
                    return f"Exceeds the maximum card count for any given family ({gm.MAX_SAME_FAMILY_CARD})"

        @classmethod
        def from_list_to_user(cls, error_list, game_mode):
            return [cls(error).to_user(game_mode) for error in error_list]


class StandardGameMode(GameMode):
    MAX_FACTION_COUNT = 1
    MIN_TOTAL_COUNT = 39
    MAX_RARE_COUNT = 15
    MAX_UNIQUE_COUNT = 3
    MAX_SAME_FAMILY_CARD = 3

    @classmethod
    def validate(cls, **kwargs):
        error_list = []

        if kwargs["faction_count"] > cls.MAX_FACTION_COUNT:
            error_list.append(cls.ErrorCode.ERR_EXCEED_FACTION_COUNT)
        if kwargs["total_count"] < cls.MIN_TOTAL_COUNT:
            error_list.append(cls.ErrorCode.ERR_NOT_ENOUGH_CARD_COUNT)
        if kwargs["rare_count"] > cls.MAX_RARE_COUNT:
            error_list.append(cls.ErrorCode.ERR_EXCEED_RARE_COUNT)
        if kwargs["unique_count"] > cls.MAX_UNIQUE_COUNT:
            error_list.append(cls.ErrorCode.ERR_EXCEED_UNIQUE_COUNT)
        if max(kwargs["family_count"].values(), default=0) > cls.MAX_SAME_FAMILY_CARD:
            error_list.append(cls.ErrorCode.ERR_EXCEED_SAME_FAMILY_COUNT)

        return error_list


class DraftGameMode(GameMode):
    MAX_FACTION_COUNT = 3
    MIN_TOTAL_COUNT = 30

    @classmethod
    def validate(cls, **kwargs):
        error_list = []

        if kwargs["faction_count"] > cls.MAX_FACTION_COUNT:
            error_list.append(cls.ErrorCode.ERR_EXCEED_FACTION_COUNT)
        if kwargs["total_count"] < cls.MIN_TOTAL_COUNT:
            error_list.append(cls.ErrorCode.ERR_NOT_ENOUGH_CARD_COUNT)

        return error_list


def update_deck_legality(deck: Deck):

    # Start at 1 to account for the hero
    total_count = 1
    rare_count = 0
    unique_count = 0
    factions = [deck.hero.faction] if deck.hero else []
    family_count = defaultdict(int)

    decklist = deck.cardindeck_set.order_by("card__reference").all()

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
    }

    error_list = StandardGameMode.validate(**data)
    deck.is_standard_legal = not bool(error_list)
    deck.standard_legality_errors = error_list

    error_list = DraftGameMode.validate(**data)
    deck.is_draft_legal = not bool(error_list)
    deck.draft_legality_errors = error_list
