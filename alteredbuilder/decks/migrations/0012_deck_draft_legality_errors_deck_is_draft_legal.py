# Generated by Django 5.0.3 on 2024-04-24 10:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("decks", "0011_alter_deck_is_standard_legal"),
    ]

    operations = [
        migrations.AddField(
            model_name="deck",
            name="draft_legality_errors",
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name="deck",
            name="is_draft_legal",
            field=models.BooleanField(null=True),
        ),
    ]
