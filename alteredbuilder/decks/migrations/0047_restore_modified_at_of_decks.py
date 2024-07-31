from django.db import migrations


def init_models(apps):
    global Deck, TempDeck
    Deck = apps.get_model("decks", "Deck")
    TempDeck = apps.get_model("decks", "TempDeck")


def restore_hero(apps, schema_editor):
    init_models(apps)

    updated_decks = []
    for deck in Deck.objects.all().order_by("pk"):
        try:
            deck.modified_at = TempDeck.objects.get(pk=deck.pk).modified_at
            updated_decks.append(deck)
        except TempDeck.DoesNotExist:
            pass
    Deck.objects.bulk_update(updated_decks, ["modified_at"])


class Migration(migrations.Migration):

    dependencies = [
        ("decks", "0046_create_model_tempdeck"),
    ]

    operations = [
        migrations.RunPython(restore_hero),
    ]
