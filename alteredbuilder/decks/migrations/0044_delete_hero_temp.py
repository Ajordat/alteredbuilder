
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("decks", "0043_restore_deck_hero_data"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="deck",
            name="hero_temp",
        ),
    ]
