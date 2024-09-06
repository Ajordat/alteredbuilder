from django.contrib.auth import get_user_model
from django.db import migrations


def init_models(apps):
    global Deck, Tag, User
    Deck = apps.get_model("decks", "Deck")
    Tag = apps.get_model("decks", "Tag")
    User = get_user_model()


def modify_official_decks(apps, schema_editor):
    init_models(apps)

    deck_filter = {"owner__username": "Equinox", "name__contains": "Official Starter"}

    aggro = Tag.objects.get(name="Aggro")
    midrange = Tag.objects.get(name="Midrange")
    control = Tag.objects.get(name="Control")

    token = Tag.objects.get(name="Token")
    combo = Tag.objects.get(name="Combo")
    disruption = Tag.objects.get(name="Disruption")

    axiom_deck = Deck.objects.get(**deck_filter, hero__faction="AX")
    axiom_deck.tags.add(midrange, token)
    axiom_deck.name = "AXIOM - Official Starter"
    axiom_deck.save()

    bravos_deck = Deck.objects.get(**deck_filter, hero__faction="BR")
    bravos_deck.tags.add(aggro, combo)
    bravos_deck.name = "BRAVOS - Official Starter"
    bravos_deck.save()

    lyra_deck = Deck.objects.get(**deck_filter, hero__faction="LY")
    lyra_deck.tags.add(midrange, combo, disruption)
    lyra_deck.name = "LYRA - Official Starter"
    lyra_deck.save()

    muna_deck = Deck.objects.get(**deck_filter, hero__faction="MU")
    muna_deck.tags.add(midrange, combo)
    muna_deck.name = "MUNA - Official Starter"
    muna_deck.save()

    ordis_deck = Deck.objects.get(**deck_filter, hero__faction="OR")
    ordis_deck.tags.add(midrange, token)
    ordis_deck.name = "ORDIS - Official Starter"
    ordis_deck.save()

    yzmir_deck = Deck.objects.get(**deck_filter, hero__faction="YZ")
    yzmir_deck.tags.add(control, disruption)
    yzmir_deck.name = "YZMIR - Official Starter"
    yzmir_deck.save()


def empty_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("decks", "0061_import_data"),
    ]

    operations = [
        migrations.RunPython(code=modify_official_decks, reverse_code=empty_reverse),
    ]
