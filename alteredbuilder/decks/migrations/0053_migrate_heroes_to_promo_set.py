from django.db import migrations


def init_models(apps):
    global Card, Set
    Card = apps.get_model("decks", "Card")
    Set = apps.get_model("decks", "Set")


def link_cards_to_sets(apps, schema_editor):
    init_models(apps)

    card_set = Set.objects.get(code="COREP")

    Card.objects.filter(reference__contains=card_set.reference_code).update(
        set=card_set
    )


def unlink_cards_to_sets(apps, schema_editor):
    init_models(apps)

    promo_set = Set.objects.get(code="COREP")
    core_set = Set.objects.get(code="CORE")
    Card.objects.filter(reference__contains=promo_set.reference_code).update(
        set=core_set
    )


class Migration(migrations.Migration):

    dependencies = [
        ("decks", "0052_convert_stats_to_int"),
    ]

    operations = [
        migrations.RunPython(link_cards_to_sets, reverse_code=unlink_cards_to_sets),
    ]
