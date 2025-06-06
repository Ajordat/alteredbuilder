# Generated by Django 5.0.8 on 2024-09-04 07:58

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    replaces = [
        ("trends", "0001_initial"),
        ("trends", "0002_herotrend"),
        ("trends", "0003_cardtrend"),
        ("trends", "0004_remove_cardtrend_count_cardtrend_hero"),
        ("trends", "0005_alter_cardtrend_faction_alter_cardtrend_hero"),
        ("trends", "0006_alter_cardtrend_options_alter_factiontrend_options_and_more"),
        ("trends", "0007_alter_herotrend_hero"),
        ("trends", "0008_decktrend"),
        ("trends", "0009_alter_decktrend_deck"),
    ]

    initial = True

    dependencies = [
        ("decks", "0034_create_promo_set"),
        ("decks", "0044_delete_hero_temp"),
        ("decks", "0058_card_created_at"),
    ]

    operations = [
        migrations.CreateModel(
            name="CardTrend",
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
                (
                    "faction",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("AX", "axiom"),
                            ("BR", "bravos"),
                            ("LY", "lyra"),
                            ("MU", "muna"),
                            ("OR", "ordis"),
                            ("YZ", "yzmir"),
                        ],
                        max_length=2,
                        null=True,
                    ),
                ),
                ("ranking", models.PositiveIntegerField(default=0)),
                ("day_count", models.PositiveIntegerField(default=7)),
                ("date", models.DateField()),
                (
                    "card",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="decks.card"
                    ),
                ),
                (
                    "hero",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="hero_trend",
                        to="decks.card",
                    ),
                ),
            ],
            options={
                "ordering": ["-date", "-hero", "-faction", "ranking"],
            },
        ),
        migrations.CreateModel(
            name="FactionTrend",
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
                (
                    "faction",
                    models.CharField(
                        choices=[
                            ("AX", "axiom"),
                            ("BR", "bravos"),
                            ("LY", "lyra"),
                            ("MU", "muna"),
                            ("OR", "ordis"),
                            ("YZ", "yzmir"),
                        ],
                        max_length=2,
                    ),
                ),
                ("count", models.PositiveIntegerField(default=0)),
                ("day_count", models.PositiveIntegerField(default=7)),
                ("date", models.DateField()),
            ],
            options={
                "ordering": ["-date", "-count"],
            },
        ),
        migrations.CreateModel(
            name="HeroTrend",
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
                ("count", models.PositiveIntegerField(default=0)),
                ("day_count", models.PositiveIntegerField(default=7)),
                ("date", models.DateField()),
                (
                    "hero",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="decks.card"
                    ),
                ),
            ],
            options={
                "ordering": ["-date", "-count"],
            },
        ),
        migrations.CreateModel(
            name="DeckTrend",
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
                (
                    "faction",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("AX", "axiom"),
                            ("BR", "bravos"),
                            ("LY", "lyra"),
                            ("MU", "muna"),
                            ("OR", "ordis"),
                            ("YZ", "yzmir"),
                        ],
                        max_length=2,
                        null=True,
                    ),
                ),
                ("ranking", models.PositiveIntegerField(default=0)),
                ("day_count", models.PositiveIntegerField(default=7)),
                ("date", models.DateField()),
                (
                    "deck",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="trend",
                        to="decks.deck",
                    ),
                ),
                (
                    "hero",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="deck_trend",
                        to="decks.card",
                    ),
                ),
            ],
            options={
                "ordering": ["-date", "-hero", "-faction", "ranking"],
            },
        ),
    ]
