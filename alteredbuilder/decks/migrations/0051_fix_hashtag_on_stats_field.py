from django.db import migrations


def init_models(apps):
    global Card
    Card = apps.get_model("decks", "Card")


def fix_stats_values(apps, schema_editor):
    init_models(apps)

    updated_cards = []
    for card in Card.objects.all():
        for field, value in card.stats.items():
            if "#" in str(value):
                card.stats[field] = value.strip("#")
                updated_cards.append(card)
    Card.objects.bulk_update(updated_cards, ["stats"])


def empty_reverse(apps, schema_editor):
    return


class Migration(migrations.Migration):

    dependencies = [
        ("decks", "0050_rename_echo_effect_temp_card_echo_effect_and_more"),
    ]

    operations = [
        migrations.RunPython(fix_stats_values, reverse_code=empty_reverse),
    ]
