from django.db import migrations
from django.db.models import Count


def init_models(apps):
    global Card
    Card = apps.get_model("decks", "Card")


def delete_unused_unique_cards(apps, schema_editor):
    init_models(apps)

    # Delete Unique cards that are not in any Deck
    Card.objects.filter(rarity="U").annotate(deck_count=Count("decks")).filter(
        deck_count=0
    ).delete()


def empty_reverse(apps, schema_editor):
    pass


def assign_subtype_to_uniques(apps, schema_editor):

    cards = Card.objects.filter(rarity="U", subtypes__isnull=True)
    subtypes_m2m = []
    for card in cards:
        family_code = "_".join(card.reference.split("_")[:-2])
        og_card = Card.objects.get(reference__startswith=family_code, rarity="C")
        for subtype in og_card.subtypes.all():
            subtypes_m2m.append(
                Card.subtypes.through(card_id=card.pk, subtype_id=subtype.pk)
            )
    Card.subtypes.through.objects.bulk_create(subtypes_m2m)


def unassign_subtype_to_uniques(apps, schema_editor):
    init_models(apps)

    Card.subtypes.through.objects.filter(card__rarity="U").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("decks", "0054_alter_subtype_options"),
    ]

    operations = [
        migrations.RunPython(delete_unused_unique_cards, reverse_code=empty_reverse),
        migrations.RunPython(
            assign_subtype_to_uniques, reverse_code=unassign_subtype_to_uniques
        ),
    ]
