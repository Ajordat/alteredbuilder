# Generated by Django 5.0.13 on 2025-03-29 23:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("recommender", "0002_trainedmodel_name"),
    ]

    operations = [
        migrations.RenameField(
            model_name="trainedmodel",
            old_name="name",
            new_name="model",
        ),
    ]
