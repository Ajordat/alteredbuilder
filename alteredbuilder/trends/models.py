from django.db import models

from decks.models import Card, Hero


class FactionTrend(models.Model):
    faction = models.CharField(max_length=2, choices=Card.Faction)

    count = models.PositiveIntegerField(default=0)
    day_count = models.PositiveIntegerField(default=7)
    date = models.DateField()


class HeroTrend(models.Model):
    hero = models.ForeignKey(Hero, on_delete=models.CASCADE)

    count = models.PositiveIntegerField(default=0)
    day_count = models.PositiveIntegerField(default=7)
    date = models.DateField()
