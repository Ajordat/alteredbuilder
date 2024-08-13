import uuid

from allauth.socialaccount.models import SocialAccount
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class UserProfile(models.Model):
    code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    bio = models.TextField(_("Biography"), blank=True)

    altered_handle = models.CharField(null=True)
    discord_public = models.BooleanField(
        _("Show Discord Handle Publicly"), default=False
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def get_absolute_url(self):
        return reverse("profile-detail", kwargs={"code": self.code})
    
    def discord_handle(self):
        try:
            social_account = SocialAccount.objects.get(user=self.user, provider="discord")
            extra_data = social_account.extra_data
            discord_username = extra_data.get("username", "")
            discord_discriminator = extra_data.get("discriminator", "")
            return f"{discord_username}#{discord_discriminator}"
        except SocialAccount.DoesNotExist:
            return None


class Follow(models.Model):
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="following", on_delete=models.CASCADE
    )
    followed = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="followers", on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.follower} follows {self.followed}"

    class Meta:
        unique_together = ["follower", "followed"]
