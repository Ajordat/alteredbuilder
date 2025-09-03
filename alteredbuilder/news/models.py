from django.db import models


# Create your models here.
class NewsItem(models.Model):

    class Sources(models.TextChoices):
        RSS = "rss", "RSS"
        YOUTUBE = "youtube", "YouTube"
        TWITCH = "twitch", "Twitch"

        @classmethod
        def as_list(cls):
            return [cls.RSS, cls.YOUTUBE, cls.TWITCH]

    source = models.CharField(max_length=16, choices=Sources)
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255, null=True)
    site = models.CharField(max_length=255)
    link = models.URLField()
    description = models.TextField(blank=True)
    thumbnail = models.URLField(blank=True, null=True)
    published_at = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-published_at"]
