# Generated by Django 5.0.7 on 2024-07-31 09:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("decks", "0044_delete_hero_temp"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="character",
            name="echo_effect_de",
        ),
        migrations.RemoveField(
            model_name="character",
            name="echo_effect_en",
        ),
        migrations.RemoveField(
            model_name="character",
            name="echo_effect_es",
        ),
        migrations.RemoveField(
            model_name="character",
            name="echo_effect_fr",
        ),
        migrations.RemoveField(
            model_name="character",
            name="echo_effect_it",
        ),
        migrations.RemoveField(
            model_name="character",
            name="main_effect_de",
        ),
        migrations.RemoveField(
            model_name="character",
            name="main_effect_en",
        ),
        migrations.RemoveField(
            model_name="character",
            name="main_effect_es",
        ),
        migrations.RemoveField(
            model_name="character",
            name="main_effect_fr",
        ),
        migrations.RemoveField(
            model_name="character",
            name="main_effect_it",
        ),
        migrations.RemoveField(
            model_name="hero",
            name="main_effect_de",
        ),
        migrations.RemoveField(
            model_name="hero",
            name="main_effect_en",
        ),
        migrations.RemoveField(
            model_name="hero",
            name="main_effect_es",
        ),
        migrations.RemoveField(
            model_name="hero",
            name="main_effect_fr",
        ),
        migrations.RemoveField(
            model_name="hero",
            name="main_effect_it",
        ),
        migrations.RemoveField(
            model_name="permanent",
            name="echo_effect_de",
        ),
        migrations.RemoveField(
            model_name="permanent",
            name="echo_effect_en",
        ),
        migrations.RemoveField(
            model_name="permanent",
            name="echo_effect_es",
        ),
        migrations.RemoveField(
            model_name="permanent",
            name="echo_effect_fr",
        ),
        migrations.RemoveField(
            model_name="permanent",
            name="echo_effect_it",
        ),
        migrations.RemoveField(
            model_name="permanent",
            name="main_effect_de",
        ),
        migrations.RemoveField(
            model_name="permanent",
            name="main_effect_en",
        ),
        migrations.RemoveField(
            model_name="permanent",
            name="main_effect_es",
        ),
        migrations.RemoveField(
            model_name="permanent",
            name="main_effect_fr",
        ),
        migrations.RemoveField(
            model_name="permanent",
            name="main_effect_it",
        ),
        migrations.RemoveField(
            model_name="spell",
            name="echo_effect_de",
        ),
        migrations.RemoveField(
            model_name="spell",
            name="echo_effect_en",
        ),
        migrations.RemoveField(
            model_name="spell",
            name="echo_effect_es",
        ),
        migrations.RemoveField(
            model_name="spell",
            name="echo_effect_fr",
        ),
        migrations.RemoveField(
            model_name="spell",
            name="echo_effect_it",
        ),
        migrations.RemoveField(
            model_name="spell",
            name="main_effect_de",
        ),
        migrations.RemoveField(
            model_name="spell",
            name="main_effect_en",
        ),
        migrations.RemoveField(
            model_name="spell",
            name="main_effect_es",
        ),
        migrations.RemoveField(
            model_name="spell",
            name="main_effect_fr",
        ),
        migrations.RemoveField(
            model_name="spell",
            name="main_effect_it",
        ),
    ]