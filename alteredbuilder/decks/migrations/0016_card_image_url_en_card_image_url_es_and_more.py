# Generated by Django 5.0.3 on 2024-05-27 14:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("decks", "0015_force_update_legality"),
    ]

    operations = [
        migrations.AddField(
            model_name="card",
            name="image_url_en",
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="card",
            name="image_url_es",
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="card",
            name="image_url_fr",
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="card",
            name="name_en",
            field=models.CharField(max_length=32, null=True),
        ),
        migrations.AddField(
            model_name="card",
            name="name_es",
            field=models.CharField(max_length=32, null=True),
        ),
        migrations.AddField(
            model_name="card",
            name="name_fr",
            field=models.CharField(max_length=32, null=True),
        ),
        migrations.AddField(
            model_name="hero",
            name="main_effect_en",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="hero",
            name="main_effect_es",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="hero",
            name="main_effect_fr",
            field=models.TextField(blank=True, null=True),
        ),
    ]