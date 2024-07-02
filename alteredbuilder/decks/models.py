import uuid

from django.conf import settings
from django.db import models
from hitcount.models import HitCountMixin


ALTERED_TCG_URL = "https://www.altered.gg"


# Create your models here.
class Card(models.Model):
    class Faction(models.TextChoices):
        AXIOM = "AX", "axiom"
        BRAVOS = "BR", "bravos"
        LYRA = "LY", "lyra"
        MUNA = "MU", "muna"
        ORDIS = "OR", "ordis"
        YZMIR = "YZ", "yzmir"

    class Type(models.TextChoices):
        SPELL = "spell"
        PERMANENT = "permanent"
        TOKEN = "token"
        CHARACTER = "character"
        HERO = "hero"
        MANA = "mana"

        @staticmethod
        def to_class(type):
            return {
                Card.Type.HERO: Hero,
                Card.Type.CHARACTER: Character,
                Card.Type.SPELL: Spell,
                Card.Type.PERMANENT: Permanent,
            }[type]

    class Rarity(models.TextChoices):
        COMMON = "C", "common"
        RARE = "R", "rare"
        UNIQUE = "U", "unique"

    reference = models.CharField(max_length=32, primary_key=True)
    name = models.CharField(max_length=48, null=False, blank=False)
    faction = models.CharField(max_length=2, choices=Faction)
    type = models.CharField(max_length=16, choices=Type)
    rarity = models.CharField(max_length=1, choices=Rarity)
    image_url = models.URLField(null=False, blank=True)

    def __str__(self) -> str:
        return f"[{self.faction}] - {self.name} ({self.rarity})"

    def get_official_link(self) -> str:
        return f"{ALTERED_TCG_URL}/cards/{self.reference}"

    class Meta:
        ordering = ["reference"]


class Hero(Card):
    reserve_count = models.SmallIntegerField(default=2)
    permanent_count = models.SmallIntegerField(default=2)
    main_effect = models.TextField(blank=True)

    def is_promo(self) -> bool:
        return "_P_" in self.reference

    def __str__(self) -> str:
        return f"{self.reference} - {self.name}"

    class Meta:
        verbose_name_plural = "heroes"


class PlayableCard(Card):
    class Meta:
        abstract = True

    main_cost = models.SmallIntegerField()
    recall_cost = models.SmallIntegerField()

    main_effect = models.TextField(blank=True)
    echo_effect = models.TextField(blank=True)


class Character(PlayableCard):
    forest_power = models.SmallIntegerField()
    mountain_power = models.SmallIntegerField()
    ocean_power = models.SmallIntegerField()

    def is_oof(self) -> bool:
        return f"_{self.faction}_" not in self.reference


class Spell(PlayableCard):
    pass


class Permanent(PlayableCard):
    pass


class Deck(models.Model, HitCountMixin):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True, max_length=2000)
    cards = models.ManyToManyField(Card, through="CardInDeck", related_name="decks")
    hero = models.ForeignKey(Hero, blank=True, null=True, on_delete=models.SET_NULL)
    is_public = models.BooleanField(default=False)

    is_standard_legal = models.BooleanField(null=True)
    standard_legality_errors = models.JSONField(default=list, blank=True)
    is_draft_legal = models.BooleanField(null=True)
    draft_legality_errors = models.JSONField(default=list, blank=True)

    love_count = models.PositiveIntegerField(default=0)

    modified_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.owner.username} - {self.name}"

    class Meta:
        indexes = [
            models.Index(fields=["-modified_at"]),
            models.Index(fields=["is_public"]),
        ]


class CardInDeck(models.Model):
    deck = models.ForeignKey(Deck, on_delete=models.CASCADE)
    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    quantity = models.PositiveSmallIntegerField(default=1)


class LovePoint(models.Model):
    deck = models.ForeignKey(Deck, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


class PrivateLink(models.Model):
    code = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    deck = models.OneToOneField(Deck, on_delete=models.CASCADE)
    last_accessed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
