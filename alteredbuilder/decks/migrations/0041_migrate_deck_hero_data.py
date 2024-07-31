
from django.db import migrations


def init_models(apps):
    global Deck
    Deck = apps.get_model("decks", "Deck")


def replicate_hero(apps, schema_editor):
    init_models(apps)

    for deck in Deck.objects.all():
        deck.hero_temp = deck.hero
        deck.save(update_fields=["hero_temp"])


class Migration(migrations.Migration):

    dependencies = [
        ("decks", "0040_create_deck_hero_temp"),
    ]

    operations = [
        migrations.RunPython(replicate_hero),
    ]
