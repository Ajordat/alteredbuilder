# Generated by Django 5.0.3 on 2024-07-01 15:23

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("decks", "0021_alter_card_name_alter_card_name_de_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="PrivateLink",
            fields=[
                (
                    "code",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("last_accessed", models.DateTimeField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "deck",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="decks.deck"
                    ),
                ),
            ],
        ),
    ]
