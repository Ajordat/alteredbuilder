# Generated by Django 5.0.7 on 2024-07-27 16:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("decks", "0035_deck_comment_count_comment"),
    ]

    operations = [
        migrations.AddField(
            model_name="comment",
            name="vote_count",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
