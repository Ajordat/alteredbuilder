from django.db import migrations


def init_models(apps):
    global Card
    Card = apps.get_model("decks", "Card")


def delete_italian_image_urls(apps, schema_editor):
    init_models(apps)

    Card.objects.filter(rarity="U").update(image_url_it="")


class Migration(migrations.Migration):

    dependencies = [
        ("decks", "0055_restart_unique_cards"),
    ]

    operations = [
        migrations.RunPython(delete_italian_image_urls),
    ]
