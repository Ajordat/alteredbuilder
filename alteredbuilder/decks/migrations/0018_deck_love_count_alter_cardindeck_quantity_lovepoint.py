# Generated by Django 5.0.3 on 2024-05-30 11:08

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("decks", "0017_character_echo_effect_en_character_echo_effect_es_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="deck",
            name="love_count",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="cardindeck",
            name="quantity",
            field=models.PositiveSmallIntegerField(default=1),
        ),
        migrations.CreateModel(
            name="LovePoint",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "deck",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="decks.deck"
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]