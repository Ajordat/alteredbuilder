from collections import defaultdict
import re

from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import F, Q
from django.utils.translation import gettext_lazy as _

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
            raise MalformedDeckException(
                _("Failed to unpack '%(line)s'") % {"line": line}
            )

        try:
            card = Card.objects.get(reference=reference)
        except Card.DoesNotExist:
            # The Card's reference needs to exist on the database
            raise MalformedDeckException(
                _("Card '%(reference)s' does not exist") % {"reference": reference}
            )

        if card.type == Card.Type.HERO:
            if not has_hero:
                try:
                    deck.hero = Hero.objects.get(reference=reference)
                except Hero.DoesNotExist:
                    # This situation would imply a database inconsistency
                    raise MalformedDeckException(
                        _("Card '%(reference)s' does not exist")
                        % {"reference": reference}
                    )
                has_hero = True
            else:
                # The Deck model requires to have exactly one Hero per Deck
                raise MalformedDeckException(
                    _("Multiple heroes present in the decklist")
                )
        else:
            if CardInDeck.objects.filter(deck=deck, card=card).exists():
                # If the card is already linked to the deck, increase its quantity
                cid = CardInDeck.objects.get(deck=deck, card=card)
                cid.quantity = F("quantity") + count
                cid.save(update_fields=["quantity"])
            else:
                # Link the Card with the Deck
                CardInDeck.objects.create(deck=deck, card=card, quantity=count)

    update_deck_legality(deck)
    deck.save()

    return deck


def get_deck_details(deck: Deck) -> dict:

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

    decklist_text = f"1 {deck.hero.reference}\n" if deck.hero else ""
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


def parse_query_syntax(query):
    filters = Q()
    hc_regex = r"hc(?P<hc_op>:|=|>|>=|<|<=)(?P<hc>\d+)"
    tags = []

    if matches := re.finditer(hc_regex, query, re.ASCII):
        for re_match in matches:
            op = re_match.group("hc_op")
            value = re_match.group("hc")
            match op:
                case "=" | ":":
                    filters &= (
                        Q(character__main_cost=value)
                        | Q(spell__main_cost=value)
                        | Q(permanent__main_cost=value)
                    )
                case "<":
                    filters &= (
                        Q(character__main_cost__lt=value)
                        | Q(spell__main_cost__lt=value)
                        | Q(permanent__main_cost__lt=value)
                    )
                case "<=":
                    filters &= (
                        Q(character__main_cost__lte=value)
                        | Q(spell__main_cost__lte=value)
                        | Q(permanent__main_cost__lte=value)
                    )
                case ">":
                    filters &= (
                        Q(character__main_cost__gt=value)
                        | Q(spell__main_cost__gt=value)
                        | Q(permanent__main_cost__gt=value)
                    )
                case ">=":
                    filters &= (
                        Q(character__main_cost__gte=value)
                        | Q(spell__main_cost__gte=value)
                        | Q(permanent__main_cost__gte=value)
                    )
            tags.append((_("hand cost"), op, value))
        query = re.sub(hc_regex, "", query)

    rc_regex = r"rc(?P<rc_op>:|=|>|>=|<|<=)(?P<rc>\d+)"

    if matches := re.finditer(rc_regex, query, re.ASCII):
        for re_match in matches:
            op = re_match.group("rc_op")
            value = re_match.group("rc")
            match op:
                case "=" | ":":
                    filters &= (
                        Q(character__recall_cost=value)
                        | Q(spell__recall_cost=value)
                        | Q(permanent__recall_cost=value)
                    )
                case "<":
                    filters &= (
                        Q(character__recall_cost__lt=value)
                        | Q(spell__recall_cost__lt=value)
                        | Q(permanent__recall_cost__lt=value)
                    )
                case "<=":
                    filters &= (
                        Q(character__recall_cost__lte=value)
                        | Q(spell__recall_cost__lte=value)
                        | Q(permanent__recall_cost__lte=value)
                    )
                case ">":
                    filters &= (
                        Q(character__recall_cost__gt=value)
                        | Q(spell__recall_cost__gt=value)
                        | Q(permanent__recall_cost__gt=value)
                    )
                case ">=":
                    filters &= (
                        Q(character__recall_cost__gte=value)
                        | Q(spell__recall_cost__gte=value)
                        | Q(permanent__recall_cost__gte=value)
                    )
            tags.append((_("reserve cost"), op, value))
        query = re.sub(rc_regex, "", query)

    x_regex = r"x:(?P<effect>\w+)"

    if matches := re.finditer(x_regex, query, re.ASCII):
        for re_match in matches:
            value = re_match.group("effect")
            filters &= (
                Q(character__main_effect__icontains=value)
                | Q(spell__main_effect__icontains=value)
                | Q(permanent__main_effect__icontains=value)
                | Q(character__echo_effect__icontains=value)
                | Q(spell__echo_effect__icontains=value)
                | Q(permanent__echo_effect__icontains=value)
            )
            tags.append((_("effect"), ": ", value))
        query = re.sub(x_regex, "", query)
    query = query.strip()
    if query:
        tags.append((_("query"), ": ", query))
        return filters & Q(name__icontains=query), tags
    else:
        return filters, tags

