# Generated by Django 5.0.7 on 2024-07-31 13:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("decks", "0048_remove_character_card_ptr_remove_hero_card_ptr_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="Subtype",
            fields=[
                ("reference", models.CharField(primary_key=True, serialize=False)),
                ("name", models.CharField()),
                ("name_de", models.CharField(null=True)),
                ("name_en", models.CharField(null=True)),
                ("name_es", models.CharField(null=True)),
                ("name_fr", models.CharField(null=True)),
                ("name_it", models.CharField(null=True)),
            ],
        ),
        migrations.AddField(
            model_name="card",
            name="subtypes",
            field=models.ManyToManyField(to="decks.subtype"),
        ),
    ]