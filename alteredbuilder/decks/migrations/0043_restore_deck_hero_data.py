
from django.db import migrations


def init_models(apps):
    global Deck
    Deck = apps.get_model("decks", "Deck")


def restore_hero(apps, schema_editor):
    init_models(apps)

    for deck in Deck.objects.all():
        deck.hero = deck.hero_temp
        deck.save(update_fields=["hero"])


class Migration(migrations.Migration):

    dependencies = [
        ("decks", "0042_update_hero_type"),
    ]

    operations = [
        migrations.RunPython(restore_hero),
    ]
