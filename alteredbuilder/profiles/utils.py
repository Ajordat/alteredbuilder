from allauth.socialaccount.models import SocialAccount


def get_discord_handle(user):
    try:
        social_account = SocialAccount.objects.get(user=user, provider="discord")
        extra_data = social_account.extra_data
        discord_username = extra_data.get("username", "")
        discord_discriminator = extra_data.get("discriminator", "")
        return f"{discord_username}#{discord_discriminator}"
    except SocialAccount.DoesNotExist:
        return None
