from django.db import models


class AccessToken(models.Model):
    service = models.CharField(unique=True)
    token = models.TextField()
    expires_at = models.DateTimeField()
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.service} token (expires at {self.expires_at})"


class Cookie(models.Model):
    service = models.CharField()
    name = models.CharField()
    value = models.TextField()
    expires = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("service", "name")

    def __str__(self):
        return f"{self.name} for {self.service}"
