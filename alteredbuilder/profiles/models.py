import uuid

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class UserProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(_("Biography"), blank=True)
    discord_public = models.BooleanField(_("Show Discord Handle Publicly"), default=False)
    created_at = models.DateTimeField(auto_now_add=True)


    def get_absolute_url(self):
        return reverse('profile-detail', kwargs={'pk': self.id})
