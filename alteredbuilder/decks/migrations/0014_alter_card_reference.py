# Generated by Django 5.0.3 on 2024-05-18 10:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("decks", "0013_alter_deck_draft_legality_errors_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="card",
            name="reference",
            field=models.CharField(max_length=32, primary_key=True, serialize=False),
        ),
    ]
