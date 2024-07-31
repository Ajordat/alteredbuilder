import uuid

from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from hitcount.models import HitCount, HitCountMixin


ALTERED_TCG_URL = "https://www.altered.gg"


class CardManager(models.Manager):
    def create_hero(
        self,
        reference,
        name,
        faction,
        image_url=None,
        card_set=None,
        main_effect=None,
        reserve_count=2,
        permanent_count=2,
    ):
        return self.create(
            reference=reference,
            name=name,
            faction=faction,
            type=Card.Type.HERO,
            image_url=image_url,
            set=card_set,
            main_effect_temp=main_effect,
            stats={"reserve_count": reserve_count, "permanent_count": permanent_count},
        )

    def create_card(
        self,
        reference,
        name,
        type,
        faction,
        rarity,
        image_url=None,
        card_set=None,
        main_effect=None,
        echo_effect=None,
        main_cost=0,
        recall_cost=0,
        forest_power=0,
        mountain_power=0,
        ocean_power=0,
    ):
        stats = {"main_cost": main_cost, "recall_cost": recall_cost}
        if type == Card.Type.CHARACTER:
            stats.update(
                {
                    "forest_power": forest_power,
                    "mountain_power": mountain_power,
                    "ocean_power": ocean_power,
                }
            )
        return self.create(
            reference=reference,
            name=name,
            faction=faction,
            type=type,
            rarity=rarity,
            image_url=image_url,
            set=card_set,
            main_effect_temp=main_effect,
            echo_effect_temp=echo_effect,
            stats=stats,
        )


class Set(models.Model):
    name = models.CharField(null=False, blank=False, unique=True)
    short_name = models.CharField(null=False, blank=False, unique=True)
    code = models.CharField(max_length=8, null=False, blank=False, unique=True)
    reference_code = models.CharField(null=False, blank=False, unique=True)

    def __str__(self) -> str:
        return self.name


class Subtype(models.Model):
    reference = models.CharField(primary_key=True)
    name = models.CharField(null=False, blank=False)

    def __str__(self) -> str:
        return self.reference


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
        TOKEN_MANA = "token_mana"

    class Rarity(models.TextChoices):
        COMMON = "C", "common"
        RARE = "R", "rare"
        UNIQUE = "U", "unique"

    reference = models.CharField(max_length=32, primary_key=True)
    name = models.CharField(max_length=48, null=False, blank=False)
    faction = models.CharField(max_length=2, choices=Faction)
    type = models.CharField(max_length=16, choices=Type)
    subtypes = models.ManyToManyField(Subtype)
    rarity = models.CharField(max_length=1, choices=Rarity)
    image_url = models.URLField(null=False, blank=True)
    set = models.ForeignKey(Set, null=True, on_delete=models.SET_NULL)

    main_effect_temp = models.TextField(blank=True)
    echo_effect_temp = models.TextField(blank=True)

    stats = models.JSONField(blank=True, default=dict)

    objects = CardManager()

    def __str__(self) -> str:
        return f"[{self.faction}] - {self.name} ({self.rarity})"

    def get_official_link(self) -> str:
        return f"{ALTERED_TCG_URL}/cards/{self.reference}"

    def get_family_code(self):
        return "_".join(self.reference.split("_")[3:5])

    def is_oof(self) -> bool:
        return f"_{self.faction}_" not in self.reference

    class Meta:
        ordering = ["reference"]


class Deck(models.Model, HitCountMixin):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True, max_length=2500)
    cards = models.ManyToManyField(Card, through="CardInDeck", related_name="decks")
    hero = models.ForeignKey(Card, blank=True, null=True, on_delete=models.SET_NULL)
    is_public = models.BooleanField(default=False)

    is_standard_legal = models.BooleanField(null=True)
    standard_legality_errors = models.JSONField(default=list, blank=True)
    is_draft_legal = models.BooleanField(null=True)
    draft_legality_errors = models.JSONField(default=list, blank=True)
    is_exalts_legal = models.BooleanField(null=True)

    love_count = models.PositiveIntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)
    hit_count_generic = GenericRelation(
        HitCount,
        object_id_field="object_pk",
        related_query_name="hit_count_generic_relation",
    )

    modified_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.owner.username} - {self.name}"

    class Meta:
        ordering = ["-modified_at"]
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

    class Meta:
        ordering = ["-created_at"]


class PrivateLink(models.Model):
    code = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    deck = models.OneToOneField(Deck, on_delete=models.CASCADE)
    last_accessed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class Comment(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    deck = models.ForeignKey(Deck, on_delete=models.CASCADE)
    body = models.TextField(blank=False, max_length=280)
    vote_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class CommentVote(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
