from django.db import migrations


def init_models(apps):
    global Deck, Card, Set
    Deck = apps.get_model("decks", "Deck")
    Card = apps.get_model("decks", "Card")
    Set = apps.get_model("decks", "Set")


def force_update_legality(apps, schema_editor):
    init_models(apps)

    core_set = Set.objects.get(code="CORE")
    promo_set = Set.objects.get(code="COREP")
    Card.objects.filter(set=promo_set).update(set=core_set, is_promo=True)
    promo_set.delete()

    Card.objects.filter(reference__contains="_A_").update(is_alt_art=True)


def empty_reverse(apps, schema_editor):

    promo_set = Set.objects.create(
        name="Promo",
        short_name="BTG-P",
        code="COREP",
        reference_code="_CORE_P_",
    )
    Card.objects.filter(reference__contains=promo_set.reference_code).update(
        set=promo_set, is_promo=False
    )
    Card.objects.filter(reference__contains="_A_").update(is_alt_art=False)


class Migration(migrations.Migration):

    dependencies = [
        ("decks", "0071_card_is_alt_art_card_is_promo"),
    ]

    operations = [
        migrations.RunPython(force_update_legality, reverse_code=empty_reverse)
    ]
