# Generated by Django 5.0.3 on 2024-07-18 14:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("decks", "0030_set_reference_code_set_short_name_alter_set_code"),
    ]

    operations = [
        migrations.AlterField(
            model_name="set",
            name="code",
            field=models.CharField(max_length=8, unique=True),
        ),
    ]