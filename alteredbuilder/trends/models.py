from django.db import models

from decks.models import Card, Hero


class FactionTrend(models.Model):
    faction = models.CharField(max_length=2, choices=Card.Faction)

    count = models.PositiveIntegerField(default=0)
    day_count = models.PositiveIntegerField(default=7)
    date = models.DateField()

    class Meta:
        ordering = ["-date", "-count"]


class HeroTrend(models.Model):
    hero = models.ForeignKey(Hero, on_delete=models.CASCADE)

    count = models.PositiveIntegerField(default=0)
    day_count = models.PositiveIntegerField(default=7)
    date = models.DateField()

    class Meta:
        ordering = ["-date", "-count"]


class CardTrend(models.Model):
    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    hero = models.ForeignKey(
        Card, on_delete=models.CASCADE, related_name="hero_trend", null=True, blank=True
    )
    faction = models.CharField(
        max_length=2, choices=Card.Faction, null=True, blank=True
    )

    ranking = models.PositiveIntegerField(default=0)

    day_count = models.PositiveIntegerField(default=7)
    date = models.DateField()

    def __str__(self) -> str:
        return f"{self.ranking} - {self.card} [{self.faction}] [{self.hero}]"

    class Meta:
        ordering = ["-date", "-hero", "-faction", "ranking"]
