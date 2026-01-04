import uuid

from django.conf import settings
from django.db import models
from django.templatetags.static import static
from django.urls import reverse


class UserProfile(models.Model):
    code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    bio = models.TextField(max_length=1000, blank=True)
    avatar = models.CharField(default="NE_DEFAULT.png")
    is_spam = models.BooleanField(default=False)

    collection = models.CharField(null=True, blank=True)

    altered_handle = models.CharField(null=True)
    discord_public = models.BooleanField(default=False)

    def get_absolute_url(self) -> str:
        return reverse("profile-detail", kwargs={"code": self.code})

    def get_followers_url(self) -> str:
        return reverse("follow-list", kwargs={"code": self.code})

    def get_follow_url(self) -> str:
        return reverse("profile-follow", kwargs={"code": self.code})

    def get_unfollow_url(self) -> str:
        return reverse("profile-unfollow", kwargs={"code": self.code})

    def get_avatar_image(self) -> str:
        return static(f"/img/avatars/{self.avatar}")


class Follow(models.Model):
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="following", on_delete=models.CASCADE
    )
    followed = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="followers", on_delete=models.CASCADE
    )
    created_at = models.DateField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.follower} follows {self.followed}"

    class Meta:
        unique_together = ["follower", "followed"]
        ordering = ["-created_at"]
