# Generated by Django 5.0.3 on 2024-04-15 15:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("decks", "0008_deck_description"),
    ]

    operations = [
        migrations.AddField(
            model_name="deck",
            name="is_standard_legal",
            field=models.BooleanField(default=True),
            preserve_default=False,
        ),
    ]
