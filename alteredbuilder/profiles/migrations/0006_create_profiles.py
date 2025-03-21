# Generated by Django 5.0.8 on 2024-08-12 15:34

from django.conf import settings
from django.db import migrations


def init_models(apps):
    global User, UserProfile
    User = apps.get_model("auth", "User")
    UserProfile = apps.get_model("profiles", "UserProfile")


def create_profiles(apps, schema_editor):
    init_models(apps)

    users_without_profiles = User.objects.filter(profile__isnull=True)

    profiles = []
    for user in users_without_profiles:
        profiles.append(UserProfile(user=user))

    UserProfile.objects.bulk_create(profiles)


class Migration(migrations.Migration):

    dependencies = [
        (
            "profiles",
            "0005_remove_userprofile_created_at_alter_userprofile_bio_and_more",
        ),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [migrations.RunPython(create_profiles)]
