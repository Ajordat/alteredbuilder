from collections import defaultdict

from django.db import migrations

from decks.game_modes import NoUniqueChampionship


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

    decklist = (
        deck.cardindeck_set.select_related("card").order_by("card__reference").all()
    )

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

    error_list = NoUniqueChampionship.validate(**data)
    deck.is_exalts_legal = not bool(error_list)


def init_models(apps):
    global Deck, Card
    Deck = apps.get_model("decks", "Deck")
    Card = apps.get_model("decks", "Card")


def force_update_legality(apps, schema_editor):
    init_models(apps)
    decks = Deck.objects.all()

    for deck in decks:
        update_deck_legality(deck)
        deck.save(update_fields=["is_exalts_legal"])


class Migration(migrations.Migration):

    dependencies = [
        ("decks", "0027_deck_is_exalts_legal"),
    ]

    operations = [migrations.RunPython(force_update_legality)]
