from collections import defaultdict
from http import HTTPStatus
import re

from django.conf import settings
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.db.models import Exists, F, IntegerField, OuterRef, Q, Subquery
from django.db.models.query import QuerySet
from django.utils.translation import activate, gettext_lazy as _
import requests

from api.utils import locale_agnostic
from config.utils import get_altered_api_locale, get_user_agent
from decks.game_modes import (
    DraftGameMode,
    GameMode,
    StandardGameMode,
    update_deck_legality,
)
from decks.models import (
    Card,
    CardInDeck,
    CardPrice,
    Deck,
    FavoriteCard,
    LovePoint,
    Subtype,
)
from decks.exceptions import AlteredAPIError, CardAlreadyExists, MalformedDeckException


# Altered's API endpoint
ALTERED_TCG_API_URL = "https://api.altered.gg/cards"
HEADERS = {"User-Agent": get_user_agent("UniqueCardImporter")}
# The API currently returns a private image link for unique cards in these languages
IMAGE_ERROR_LOCALES = ["es", "it", "de"]

OPERATOR_TO_HTML = {
    ":": ":",
    "=": " =",
    "<": " &lt;",
    "<=": " &le;",
    ">": " &gt;",
    ">=": " &ge;",
}
TRIGGER_TRANSLATION = {
    "etb": "{J}",
    "hand": "{H}",
    "reserve": "{R}",
    "discard": "{D}",
    "exhaust": "{T}",
    "passive": "{I}",
}


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
                # Translators: This is logged when the provided text decklist has an invalid format
                _("Failed to unpack '%(line)s'")
                % {"line": line}
            )

        try:
            card = Card.objects.get(reference=reference)
        except Card.DoesNotExist:
            try:
                card = import_unique_card(reference)
                FavoriteCard.objects.get_or_create(user=user, card=card)
                print(f"Created card '{reference}'")
            except AlteredAPIError:
                # The Card's reference needs to exist on the database
                raise MalformedDeckException(
                    _("Card '%(reference)s' wasn't found and couldn't be imported")
                    % {"reference": reference}
                )

        if card.type == Card.Type.HERO:
            if not has_hero:
                deck.hero = card
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

    cid_queryset: QuerySet[CardInDeck] = deck.cardindeck_set
    decklist = (
        cid_queryset.select_related("card")
        .prefetch_related("card__prices")
        .annotate(
            last_price=Subquery(
                CardPrice.objects.filter(card=OuterRef("card__pk"))
                .order_by("-date")
                .values("price")[:1],
                output_field=IntegerField(),
            )
        )
        .order_by("card__reference")
        .all()
    )

    hand_counter = defaultdict(int)
    recall_counter = defaultdict(int)
    rarity_counter = defaultdict(int)
    power_counter = defaultdict(int)

    # This dictionary will hold all metadata based on the card's type by using the
    # type as a key
    type_stats = {
        Card.Type.CHARACTER: [[], 0],
        Card.Type.SPELL: [[], 0],
        Card.Type.LANDMARK_PERMANENT: [[], 0],
        Card.Type.EXPEDITION_PERMANENT: [[], 0],
    }
    for cid in decklist:
        # Append the card to its own type card list
        type_stats[cid.card.type][0].append((cid.quantity, cid.card, cid.last_price))
        # Count the card count of the card's type
        type_stats[cid.card.type][1] += cid.quantity
        # Count the amount of cards with the same hand cost
        hand_counter[cid.card.stats["main_cost"]] += cid.quantity
        # Count the amount of cards with the same recall cost
        recall_counter[cid.card.stats["recall_cost"]] += cid.quantity
        # Count the amount of cards with the same rarity
        rarity_counter[cid.card.rarity] += cid.quantity
        power_counter["forest"] += cid.card.stats.get("forest_power", 0) * cid.quantity
        power_counter["mountain"] += (
            cid.card.stats.get("mountain_power", 0) * cid.quantity
        )
        power_counter["ocean"] += cid.card.stats.get("ocean_power", 0) * cid.quantity

    decklist_text = f"1 {deck.hero.reference}\n" if deck.hero else ""
    decklist_text += "\n".join(
        [f"{cid.quantity} {cid.card.reference}" for cid in decklist]
    )

    return {
        "decklist": decklist_text,
        "character_list": sorted(
            type_stats[Card.Type.CHARACTER][0], key=sort_by_mana_cost
        ),
        "spell_list": sorted(type_stats[Card.Type.SPELL][0], key=sort_by_mana_cost),
        "permanent_list": sorted(
            type_stats[Card.Type.LANDMARK_PERMANENT][0]
            + type_stats[Card.Type.EXPEDITION_PERMANENT][0],
            key=sort_by_mana_cost,
        ),
        "stats": {
            "type_distribution": {
                "characters": type_stats[Card.Type.CHARACTER][1],
                "spells": type_stats[Card.Type.SPELL][1],
                "permanents": type_stats[Card.Type.LANDMARK_PERMANENT][1]
                + type_stats[Card.Type.EXPEDITION_PERMANENT][1],
            },
            "total_count": type_stats[Card.Type.CHARACTER][1]
            + type_stats[Card.Type.SPELL][1]
            + type_stats[Card.Type.LANDMARK_PERMANENT][1]
            + type_stats[Card.Type.EXPEDITION_PERMANENT][1],
            "mana_distribution": {
                "hand": hand_counter,
                "recall": recall_counter,
            },
            "rarity_distribution": {
                "common": rarity_counter[Card.Rarity.COMMON],
                "rare": rarity_counter[Card.Rarity.RARE],
                "unique": rarity_counter[Card.Rarity.UNIQUE],
            },
            "region_distribution": power_counter,
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


def sort_by_mana_cost(row):
    return row[1].stats["main_cost"], row[1].stats["recall_cost"]


@transaction.atomic
def patch_deck(deck: Deck, name: str, changes: dict[str, int]) -> None:
    deck.name = name

    for card_reference, quantity in changes.items():
        try:
            card = Card.objects.get(reference=card_reference)
            if card.type == Card.Type.HERO:
                if quantity > 0:
                    deck.hero = card
                elif quantity == 0 and deck.hero == card:
                    deck.hero = None
            else:
                cid = CardInDeck.objects.get(card=card, deck=deck)
                if quantity > 0:
                    cid.quantity = quantity
                    cid.save()
                else:
                    cid.delete()
        except Card.DoesNotExist:
            continue
        except CardInDeck.DoesNotExist:
            if quantity > 0:
                CardInDeck.objects.create(card=card, deck=deck, quantity=quantity)


def remove_card_from_deck(deck: Deck, reference: str) -> None:
    card = Card.objects.get(reference=reference)
    if card.type == Card.Type.HERO and deck.hero.reference == card.reference:
        # If it's the Deck's hero, remove the reference
        deck.hero = None
    else:
        # Retrieve the CiD and delete it
        cid = CardInDeck.objects.get(deck=deck, card=card)
        cid.delete()


def parse_card_query_syntax(
    qs: QuerySet[Card], query: str
) -> tuple[QuerySet[Card], list[(str, str, str)], bool]:
    filters = Q()
    tags = []

    ref_regex = r"ref:(?P<reference>\w+)"

    if matches := re.finditer(ref_regex, query, re.ASCII):
        for re_match in matches:
            reference = re_match.group("reference")
            tags.append((_("reference"), ":", reference))
            return qs.filter(reference=reference), tags, True

    hc_regex = r"hc(?P<hc_op>:|=|>|>=|<|<=)(?P<hc>\d+)"

    if matches := re.finditer(hc_regex, query, re.ASCII):
        for re_match in matches:
            op = re_match.group("hc_op")
            value = int(re_match.group("hc"))
            match op:
                case "=" | ":":
                    filters &= Q(stats__main_cost=value)
                case "<":
                    filters &= Q(stats__main_cost__lt=value)
                case "<=":
                    filters &= Q(stats__main_cost__lte=value)
                case ">":
                    filters &= Q(stats__main_cost__gt=value)
                case ">=":
                    filters &= Q(stats__main_cost__gte=value)
            tags.append((_("hand cost"), OPERATOR_TO_HTML[op], str(value)))
        query = re.sub(hc_regex, "", query)

    rc_regex = r"rc(?P<rc_op>:|=|>|>=|<|<=)(?P<rc>\d+)"

    if matches := re.finditer(rc_regex, query, re.ASCII):
        for re_match in matches:
            op = re_match.group("rc_op")
            value = int(re_match.group("rc"))
            match op:
                case "=" | ":":
                    filters &= Q(stats__recall_cost=value)
                case "<":
                    filters &= Q(stats__recall_cost__lt=value)
                case "<=":
                    filters &= Q(stats__recall_cost__lte=value)
                case ">":
                    filters &= Q(stats__recall_cost__gt=value)
                case ">=":
                    filters &= Q(stats__recall_cost__gte=value)
            tags.append((_("reserve cost"), OPERATOR_TO_HTML[op], str(value)))
        query = re.sub(rc_regex, "", query)

    x_regex = r"x:(?P<effect>\w+)"

    if matches := re.finditer(x_regex, query):
        for re_match in matches:
            value = re_match.group("effect")
            filters &= Q(main_effect__icontains=value) | Q(echo_effect__icontains=value)
            tags.append((_("ability"), ":", value))
        query = re.sub(x_regex, "", query)

    st_regex = r"st:(?P<subtype>\w+)"

    if matches := re.finditer(st_regex, query):
        for re_match in matches:
            value = re_match.group("subtype")
            qs = qs.filter(
                Exists(
                    Subtype.objects.filter(card=OuterRef("pk"), name__icontains=value)
                )
            )
            tags.append((_("subtype"), ":", value))
        query = re.sub(st_regex, "", query)

    t_regex = r"t:(?P<trigger>\w+)"

    if matches := re.finditer(t_regex, query):
        for re_match in matches:
            try:
                trigger = re_match.group("trigger")
                value = TRIGGER_TRANSLATION[trigger]
                if trigger in ["discard", "passive"]:
                    filters &= Q(echo_effect__contains=value)
                else:
                    filters &= Q(main_effect__contains=value)
                tags.append((_("trigger"), ":", trigger))
            except KeyError:
                continue
        query = re.sub(t_regex, "", query)

    query = query.strip()
    if query:
        tags.append((_("query"), ":", query))
        return qs.filter(filters & Q(name__icontains=query)), tags, False
    else:
        return qs.filter(filters), tags, False


@locale_agnostic
def import_unique_card(reference: str) -> Card:  # pragma: no cover

    # Check if the card already exists in the database
    if Card.objects.filter(reference=reference).exists():
        raise CardAlreadyExists

    # Fetch the card data from the official API
    api_url = f"{ALTERED_TCG_API_URL}/{reference}/"
    response = requests.get(api_url, headers=HEADERS)

    if response.status_code != HTTPStatus.OK:
        match response.status_code:
            case HTTPStatus.UNAUTHORIZED:
                msg = f"The card {reference} is not public"
            case HTTPStatus.NOT_FOUND:
                msg = f"The card {reference} does not exist"
            case _:
                msg = "Couldn't access the Altered API"
        raise AlteredAPIError(msg, status_code=response.status_code)

    card_data = response.json()
    family = "_".join(reference.split("_")[:-2])
    try:
        og_card = Card.objects.filter(
            reference__startswith=family, rarity=Card.Rarity.COMMON
        ).get()
    except Card.DoesNotExist:
        raise AlteredAPIError(
            f"The card family '{family}' does not exist in the database",
            status_code=HTTPStatus.NOT_FOUND,
        )
    card_dict = {
        "reference": reference,
        "name": og_card.name,
        "faction": card_data["mainFaction"]["reference"],
        "type": Card.Type.CHARACTER,
        "rarity": Card.Rarity.UNIQUE,
        "image_url": card_data["imagePath"],
        "set": og_card.set,
        "stats": {
            "main_cost": int(card_data["elements"]["MAIN_COST"]),
            "recall_cost": int(card_data["elements"]["RECALL_COST"]),
            "forest_power": int(card_data["elements"]["FOREST_POWER"]),
            "mountain_power": int(card_data["elements"]["MOUNTAIN_POWER"]),
            "ocean_power": int(card_data["elements"]["OCEAN_POWER"]),
        },
    }
    if "MAIN_EFFECT" in card_data["elements"]:
        card_dict["main_effect"] = card_data["elements"]["MAIN_EFFECT"]
    if "ECHO_EFFECT" in card_data["elements"]:
        card_dict["echo_effect"] = card_data["elements"]["ECHO_EFFECT"]

    card = Card(**card_dict)

    for language, _ in settings.LANGUAGES:  # noqa: F402
        if language == settings.LANGUAGE_CODE:
            continue
        activate(language)
        locale_code = get_altered_api_locale(language)
        headers = {"Accept-Language": locale_code}
        response = requests.get(api_url, headers=headers)
        card_data = response.json()
        card.name = og_card.name

        if "MAIN_EFFECT" in card_data["elements"]:
            card.main_effect = card_data["elements"]["MAIN_EFFECT"]
        if "ECHO_EFFECT" in card_data["elements"]:
            card.echo_effect = card_data["elements"]["ECHO_EFFECT"]
        if language not in IMAGE_ERROR_LOCALES:
            if "imagePath" in card_data:
                card.image_url = card_data["imagePath"]
            elif "allImagePath" in card_data:
                card.image_url = card_data["allImagePath"].get(locale_code)

    try:
        with transaction.atomic():
            card.save()
            card.subtypes.add(*og_card.subtypes.all())
    except IntegrityError as e:
        if 'duplicate key value violates unique constraint "decks_card_pkey"' in str(e):
            # This can happen if the user attempts to import a deck and submits
            # another import with the same unique card while it hasn't been fully
            # imported.
            # I could use `get_or_create` but that would imply dealing with the
            # i18n attributes of the Card table and I don't want to.
            print("Duplicate primary key detected. Skip the commit into the db.")
            return Card.objects.get(reference=card.reference)
        else:
            raise

    return card


def filter_by_query(qs: QuerySet[Deck], query: str) -> QuerySet[Deck]:
    filters = Q()
    tags = []

    if query:
        t_regex = r"u:(?P<username>[\w\.-@]+)"

        if matches := re.finditer(t_regex, query):
            for re_match in matches:
                username = re_match.group("username")
                filters &= Q(owner__username__iexact=username)
                tags.append((_("user"), ":", username))
            query = re.sub(t_regex, "", query)

        h_regex = r"h:(?P<hero>\w+)"

        if matches := re.finditer(h_regex, query):
            for re_match in matches:
                hero = re_match.group("hero")
                filters &= Q(hero__name__icontains=hero)
                tags.append((_("hero"), ":", hero))
            query = re.sub(h_regex, "", query)

        ref_regex = r"ref:(?P<reference>\w+)"

        if matches := re.finditer(ref_regex, query):
            for re_match in matches:
                reference = re_match.group("reference")
                filters &= Q(cards__reference=reference)
                tags.append((_("reference"), ":", reference))
            query = re.sub(ref_regex, "", query)

        query = query.strip()
        if query:
            tags.append((_("query"), ":", query))
            qs = qs.filter(filters & Q(name__icontains=query))
        else:
            qs = qs.filter(filters)

    return qs, tags if tags else None


def filter_by_faction(qs: QuerySet[Deck], factions: str) -> QuerySet[Deck]:
    if factions:
        try:
            factions = [Card.Faction(faction) for faction in factions.split(",")]
            qs = qs.filter(hero__faction__in=factions)
        except ValueError:
            pass
    return qs


def filter_by_legality(qs: QuerySet[Deck], legality: str) -> QuerySet[Deck]:

    if legality:
        legality = legality.split(",")
        if "standard" in legality:
            qs = qs.filter(is_standard_legal=True)
        elif "draft" in legality:
            qs = qs.filter(is_draft_legal=True)
        if "exalts" in legality:
            qs = qs.filter(is_exalts_legal=True)
        if "doubles" in legality:
            qs = qs.filter(is_doubles_legal=True)

    return qs


def filter_by_tags(qs: QuerySet[Deck], tags: str) -> QuerySet[Deck]:
    if tags:
        qs = qs.filter(tags__name__in=tags.split(",")).distinct()
    return qs


def filter_by_other(qs: QuerySet[Deck], other_filters: str, user) -> QuerySet[Deck]:
    if other_filters:
        other_filters = other_filters.split(",")
        if "loved" in other_filters:
            try:
                lp = LovePoint.objects.filter(user=user)
                qs = qs.filter(id__in=lp.values_list("deck_id", flat=True))
            except TypeError:
                pass
        if "description" in other_filters:
            qs = qs.exclude(description="")
    return qs


def card_code_from_reference(reference: str) -> str:
    return "_".join(reference.split("_")[3:6])


def family_code_from_reference(reference: str) -> str:
    return "_".join(reference.split("_")[3:5])
