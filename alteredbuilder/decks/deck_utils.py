from collections import defaultdict
from django.contrib.auth.models import User
from django.db import transaction
from .game_modes import DraftGameMode, GameMode, StandardGameMode, update_deck_legality
from .models import Card, CardInDeck, Deck, Hero
from .exceptions import MalformedDeckException


@transaction.atomic
def create_new_deck(user: User, deck_form: dict) -> Deck:
    """Method to validate the clean data from a DecklistForm and create it if all input
    is valid.

    Args:
        user (User): The Deck's owner.
        deck_form (dict): Clean data from a DecklistForm.

    Raises:
        MalformedDeckException: If the decklist is invalid.

    Returns:
        Deck: The resulting object.
    """
    decklist = deck_form["decklist"]
    deck = Deck.objects.create(
        name=deck_form["name"],
        owner=user,
        is_public=deck_form["is_public"],
        description=deck_form["description"],
    )
    has_hero = False

    for line in decklist.splitlines():
        # For each line, it is needed to:
        # * Validate its format
        # * Search the card reference on the database
        #   - If it's a Hero, assign it to the Deck's Hero
        #   - Otherwise append it to the list of cards
        try:
            count, reference = line.split()
            count = int(count)
        except ValueError:
            # The form validator only checks if there's at least one
            # line with the correct format
            raise MalformedDeckException(f"Failed to unpack '{line}'")

        try:
            card = Card.objects.get(reference=reference)
        except Card.DoesNotExist:
            # The Card's reference needs to exist on the database
            raise MalformedDeckException(f"Card '{reference}' does not exist")

        if card.type == Card.Type.HERO:
            if not has_hero:
                try:
                    deck.hero = Hero.objects.get(reference=reference)
                except Hero.DoesNotExist:
                    # This situation would imply a database inconsistency
                    raise MalformedDeckException(f"Card '{reference}' does not exist")
                has_hero = True
            else:
                # The Deck model requires to have exactly one Hero per Deck
                raise MalformedDeckException("Multiple heroes present in the decklist")
        else:
            # Link the Card with the Deck
            CardInDeck.objects.create(deck=deck, card=card, quantity=count)

    if not has_hero:
        # The Deck model requires to have exactly one Hero per Deck
        raise MalformedDeckException("Missing hero in decklist")

    update_deck_legality(deck)
    deck.save()

    return deck


def get_deck_details(deck):

    decklist = (
        deck.cardindeck_set.select_related(
            "card__character", "card__spell", "card__permanent"
        )
        .order_by("card__reference")
        .all()
    )

    hand_counter = defaultdict(int)
    recall_counter = defaultdict(int)
    rarity_counter = defaultdict(int)

    # This dictionary will hold all metadata based on the card's type by using the
    # type as a key
    d = {
        Card.Type.CHARACTER: [[], 0, "character"],
        Card.Type.SPELL: [[], 0, "spell"],
        Card.Type.PERMANENT: [[], 0, "permanent"],
    }
    for cid in decklist:
        # Append the card to its own type card list
        d[cid.card.type][0].append((cid.quantity, cid.card))
        # Count the card count of the card's type
        d[cid.card.type][1] += cid.quantity
        # Count the amount of cards with the same hand cost
        hand_counter[getattr(cid.card, d[cid.card.type][2]).main_cost] += cid.quantity
        # Count the amount of cards with the same recall cost
        recall_counter[
            getattr(cid.card, d[cid.card.type][2]).recall_cost
        ] += cid.quantity
        # Count the amount of cards with the same rarity
        rarity_counter[cid.card.rarity] += cid.quantity

    decklist_text = f"1 {deck.hero.reference}\n"
    decklist_text += "\n".join(
        [f"{cid.quantity} {cid.card.reference}" for cid in decklist]
    )
    return {
        "decklist": decklist_text,
        "character_list": d[Card.Type.CHARACTER][0],
        "spell_list": d[Card.Type.SPELL][0],
        "permanent_list": d[Card.Type.PERMANENT][0],
        "stats": {
            "type_distribution": {
                "characters": d[Card.Type.CHARACTER][1],
                "spells": d[Card.Type.SPELL][1],
                "permanents": d[Card.Type.PERMANENT][1],
            },
            "total_count": d[Card.Type.CHARACTER][1]
            + d[Card.Type.SPELL][1]
            + d[Card.Type.PERMANENT][1],
            "mana_distribution": {
                "hand": hand_counter,
                "recall": recall_counter,
            },
            "rarity_distribution": {
                "common": rarity_counter[Card.Rarity.COMMON],
                "rare": rarity_counter[Card.Rarity.RARE],
                "unique": rarity_counter[Card.Rarity.UNIQUE],
            },
        },
        "legality": {
            "standard": {
                "is_legal": deck.is_standard_legal,
                "errors": GameMode.ErrorCode.from_list_to_user(
                    deck.standard_legality_errors, StandardGameMode
                ),
            },
            "draft": {
                "is_legal": deck.is_draft_legal,
                "errors": GameMode.ErrorCode.from_list_to_user(
                    deck.draft_legality_errors, DraftGameMode
                ),
            },
        },
    }
