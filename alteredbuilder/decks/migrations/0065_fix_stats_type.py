from django.db import migrations


def init_models(apps):
    global Card
    Card = apps.get_model("decks", "Card")


def fix_stats_type(apps, schema_editor):
    init_models(apps)

    updated_cards = []

    for card in Card.objects.all():
        updated = False
        for key, value in card.stats.items():
            if isinstance(value, str):
                card.stats[key] = int(value)
                updated = True
        if updated:
            updated_cards.append(card)

    Card.objects.bulk_update(updated_cards, ["stats"])


def empty_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("decks", "0064_card_decks_card_rarity_fefb3f_idx_and_more"),
    ]

    operations = [
        migrations.RunPython(code=fix_stats_type, reverse_code=empty_reverse),
    ]
