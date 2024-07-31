
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("decks", "0041_migrate_deck_hero_data"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="deck",
            name="hero",
        ),
        migrations.AddField(
            model_name="deck",
            name="hero",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="decks.card",
            ),
        ),
    ]
