# Generated by Django 5.0.14 on 2025-06-01 16:47

from django.conf import settings
from django.db import migrations, models
from gettext import pgettext


def init_models(apps):
    global Set
    Set = apps.get_model("decks", "Set")


def translate_sets(apps, schema_editor):
    init_models(apps)

    Set.objects.filter(code="CORE").update(
        name_de="Jenseits der Tore",
        name_en="Beyond the Gates",
        name_es="Más Allá de las Puertas",
        name_fr="Au-delà Des Portes",
        name_it="Oltre i Cancelli",
    )
    Set.objects.filter(code="COREKS").update(
        name_de=None,
        name_en="Kickstarter Edition",
        name_es="Edición Kickstarter",
        name_fr="Kickstarter Édition",
        name_it=None,
    )
    Set.objects.filter(code="ALIZE").update(
        name_de="Prüfung des Eises",
        name_en="Trial by Frost",
        name_es="La Prueba de Hielo",
        name_fr="Épreuve du Froid",
        name_it="Prova del Gelo",
    )
    Set.objects.filter(code="BISE").update(
        name_de="Geflüster aus dem Laberinth",
        name_en="Whispers from the Maze",
        name_es="Susurros del Laberinto",
        name_fr="Murmure du Labyrinthe",
        name_it="Sussurri dal Labirinto",
    )


def empty_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("decks", "0078_alter_cardprice_card"),
    ]

    operations = [
        migrations.AddField(
            model_name="set",
            name="name_de",
            field=models.CharField(null=True, unique=True),
        ),
        migrations.AddField(
            model_name="set",
            name="name_en",
            field=models.CharField(null=True, unique=True),
        ),
        migrations.AddField(
            model_name="set",
            name="name_es",
            field=models.CharField(null=True, unique=True),
        ),
        migrations.AddField(
            model_name="set",
            name="name_fr",
            field=models.CharField(null=True, unique=True),
        ),
        migrations.AddField(
            model_name="set",
            name="name_it",
            field=models.CharField(null=True, unique=True),
        ),
        migrations.RunPython(translate_sets, reverse_code=empty_reverse),
    ]
