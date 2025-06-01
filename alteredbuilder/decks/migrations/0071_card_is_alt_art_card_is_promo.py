from django.conf import settings
from django.db import migrations
from django.core.management import call_command


def init_models(apps):
    global Card, CardInDeck, Deck, Set, Subtype
    Set = apps.get_model("decks", "Set")
    Subtype = apps.get_model("decks", "Subtype")
    Card = apps.get_model("decks", "Card")
    Deck = apps.get_model("decks", "Deck")
    CardInDeck = apps.get_model("decks", "CardInDeck")


def import_data(apps, schema_editor):
    init_models(apps)

    if not settings.DEBUG:
        return

    Set.objects.all().delete()
    Subtype.objects.all().delete()
    Card.objects.all().delete()
    Deck.objects.all().delete()
    CardInDeck.objects.all().delete()
    # Probably these commands fail. This happens because loaddata seems to take the
    # current version of the model, despite being in a migration and all that data
    # being from a previous version of the models.
    # I should find a way to make these imports respecting the model version.
    call_command("loaddata", "sets_04092024", verbosity=0)
    call_command("loaddata", "subtypes_04092024", verbosity=0)
    call_command("loaddata", "cards_04092024", verbosity=0)
    call_command("loaddata", "decks_02022025", verbosity=0)
    call_command("loaddata", "cardindecks_04092024", verbosity=0)


def delete_data(apps, schema_editor):
    init_models(apps)

    if not settings.DEBUG:
        return

    Set.objects.all().delete()
    Subtype.objects.all().delete()
    Card.objects.all().delete()
    Deck.objects.all().delete()
    CardInDeck.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("decks", "0070_import_data"),
    ]

    operations = [
        migrations.RunPython(code=import_data, reverse_code=delete_data),
    ]
