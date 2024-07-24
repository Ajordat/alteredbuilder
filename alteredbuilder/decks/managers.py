from django.db import models


class DeckQuerySet(models.QuerySet):
    def with_faction(self, faction):
        if faction:
            return self.filter(hero__faction=faction)
        return self

    def with_hero(self, hero_name):
        if hero_name:
            return self.filter(hero__name__startswith=hero_name)
        return self


class DeckManager(models.Manager):
    def get_queryset(self) -> models.QuerySet:
        return DeckQuerySet(self.model, using=self._db)


class LovePointQuerySet(models.QuerySet):
    def with_faction(self, faction):
        if faction:
            return self.filter(deck__hero__faction=faction)
        return self


class LovePointManager(models.Manager):
    def get_queryset(self) -> models.QuerySet:
        return LovePointQuerySet(self.model, using=self._db)


class CardInDeckQuerySet(models.QuerySet):
    def with_faction(self, faction):
        if faction:
            return self.filter(card__faction=faction)
        return self

    def with_hero(self, hero_name):
        if hero_name:
            return self.filter(deck__hero__name__startswith=hero_name)
        return self


class CardInDeckManager(models.Manager):
    def get_queryset(self) -> models.QuerySet:
        return CardInDeckQuerySet(self.model, using=self._db)
