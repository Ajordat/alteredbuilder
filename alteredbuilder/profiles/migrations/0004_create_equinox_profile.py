# Generated by Django 5.0.8 on 2024-08-12 15:34

from django.conf import settings
from django.db import migrations


def init_models(apps):
    global Deck, User, UserProfile
    Deck = apps.get_model("decks", "Deck")
    User = apps.get_model("auth", "User")
    UserProfile = apps.get_model("profiles", "UserProfile")


def create_equinox_profile(apps, schema_editor):
    init_models(apps)

    equinox_user = User.objects.create_user("Equinox")
    try:
        admin_user = User.objects.get(username="admin")

        equinox_user.date_joined = admin_user.date_joined
        Deck.objects.filter(owner=admin_user, is_public=True).update(owner=equinox_user)
    except User.DoesNotExist:
        pass
    equinox_user.save()
    equinox_profile = UserProfile.objects.create(user=equinox_user)

    equinox_profile.bio = """Hi! [[hand]]

[[etb]] This account is made by [Ajordat](https://discordapp.com/users/501840797159653389), not Equinox.

It is used to host the pre-constructed decks made by Equinox."""
    equinox_profile.save()


class Migration(migrations.Migration):

    dependencies = [
        ("profiles", "0003_follow"),
        ("decks", "0060_create_tags"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [migrations.RunPython(create_equinox_profile)]
