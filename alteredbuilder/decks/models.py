import uuid

from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.urls import reverse
from hitcount.models import HitCount, HitCountMixin


ALTERED_TCG_URL = "https://www.altered.gg"
CARD_DISPLAY_URL_FORMAT = "https://altered-prod-eu.s3.amazonaws.com/Art/CORE/CARDS/ALT_CORE_B_{}/ALT_CORE_B_{}_WEB.jpg"


class CardManager(models.Manager):

    def create_card(self, **kwargs):
        if kwargs["type"] == Card.Type.HERO:
            return self.create_hero(**kwargs)
        else:
            return self.create_playable_card(**kwargs)

    def create_hero(
        self,
        reference,
        name,
        faction,
        image_url=None,
        set=None,
        main_effect=None,
        reserve_count=2,
        permanent_count=2,
        **kwargs,
    ):
        return self.create(
            reference=reference,
            name=name,
            faction=faction,
            type=Card.Type.HERO,
            image_url=image_url,
            set=set,
            main_effect=main_effect,
            stats={"reserve_count": reserve_count, "permanent_count": permanent_count},
            **kwargs,
        )

    def create_playable_card(
        self,
        reference,
        name,
        type,
        faction,
        rarity,
        image_url=None,
        set=None,
        main_effect=None,
        echo_effect=None,
        main_cost=0,
        recall_cost=0,
        forest_power=0,
        mountain_power=0,
        ocean_power=0,
        is_promo=False,
        is_alt_art=False,
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
            set=set,
            main_effect=main_effect,
            echo_effect=echo_effect,
            stats=stats,
            is_promo=is_promo,
            is_alt_art=is_alt_art,
        )


class Set(models.Model):
    name = models.CharField(null=False, blank=False, unique=True)
    short_name = models.CharField(null=False, blank=False, unique=True)
    code = models.CharField(max_length=8, null=False, blank=False, unique=True)
    reference_code = models.CharField(null=False, blank=False, unique=True)
    release_date = models.DateField(null=False, blank=False)

    def __str__(self) -> str:
        return self.name


class Subtype(models.Model):
    reference = models.CharField(primary_key=True)
    name = models.CharField(null=False, blank=False)

    def __str__(self) -> str:
        return self.reference

    class Meta:
        ordering = ["name"]


# Create your models here.
class Card(models.Model):
    class Faction(models.TextChoices):
        AXIOM = "AX", "axiom"
        BRAVOS = "BR", "bravos"
        LYRA = "LY", "lyra"
        MUNA = "MU", "muna"
        ORDIS = "OR", "ordis"
        YZMIR = "YZ", "yzmir"

        @classmethod
        def as_list(cls):
            return [cls.AXIOM, cls.BRAVOS, cls.LYRA, cls.MUNA, cls.ORDIS, cls.YZMIR]

    class Type(models.TextChoices):
        SPELL = "spell"
        LANDMARK_PERMANENT = "landmark_permanent"
        EXPEDITION_PERMANENT = "expedition_permanent"
        TOKEN = "token"
        CHARACTER = "character"
        HERO = "hero"
        TOKEN_MANA = "token_mana"

    class Rarity(models.TextChoices):
        COMMON = "C", "common"
        RARE = "R", "rare"
        UNIQUE = "U", "unique"

        @classmethod
        def as_list(cls):
            return [cls.COMMON, cls.RARE, cls.UNIQUE]

    reference = models.CharField(primary_key=True)
    name = models.CharField(null=False, blank=False)
    faction = models.CharField(max_length=2, choices=Faction)
    type = models.CharField(choices=Type)
    subtypes = models.ManyToManyField(Subtype, blank=True)
    rarity = models.CharField(max_length=1, choices=Rarity)
    image_url = models.URLField(null=False, blank=True)
    set = models.ForeignKey(Set, null=True, on_delete=models.SET_NULL)

    main_effect = models.TextField(blank=True)
    echo_effect = models.TextField(blank=True)

    is_promo = models.BooleanField(default=False)
    is_alt_art = models.BooleanField(default=False)

    stats = models.JSONField(blank=True, default=dict)

    created_at = models.DateTimeField(auto_now_add=True, null=True)

    objects = CardManager()

    @staticmethod
    def get_base_fields():
        return ["name", "faction", "image_url", "set", "is_promo", "is_alt_art"]

    def __str__(self) -> str:
        return f"[{self.faction}] - {self.name} ({self.rarity})"

    def get_official_link(self) -> str:
        return f"{ALTERED_TCG_URL}/cards/{self.reference}"

    def get_family_code(self) -> str:
        return "_".join(self.reference.split("_")[3:5])

    def get_card_code(self) -> str:
        return "_".join(self.reference.split("_")[3:6])

    def get_display_image(self) -> str:
        short_reference = self.reference[-7:]
        return CARD_DISPLAY_URL_FORMAT.format(short_reference[:-2], short_reference)

    def is_oof(self) -> bool:
        return f"_{self.faction}_" not in self.reference

    class Meta:
        ordering = ["reference"]
        indexes = [models.Index(fields=["rarity"]), models.Index(fields=["faction"])]


class Tag(models.Model):
    class Type(models.TextChoices):
        TYPE = "TY", "type"
        SUBTYPE = "SU", "subtype"

    name = models.CharField(unique=True)
    description = models.CharField(blank=True)
    type = models.CharField(max_length=2, choices=Type)

    def __str__(self) -> str:
        return self.name

    class Meta:
        ordering = ["-type", "name"]


class Deck(models.Model, HitCountMixin):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True, max_length=3000)
    cards = models.ManyToManyField(Card, through="CardInDeck", related_name="decks")
    hero = models.ForeignKey(Card, blank=True, null=True, on_delete=models.SET_NULL)
    is_public = models.BooleanField(default=False)

    is_standard_legal = models.BooleanField(null=True)
    standard_legality_errors = models.JSONField(default=list, blank=True)
    is_draft_legal = models.BooleanField(null=True)
    draft_legality_errors = models.JSONField(default=list, blank=True)
    is_exalts_legal = models.BooleanField(null=True)
    is_doubles_legal = models.BooleanField(null=True)

    love_count = models.PositiveIntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)
    copy_count = models.PositiveIntegerField(default=0)
    hit_count_generic = GenericRelation(
        HitCount,
        object_id_field="object_pk",
        related_query_name="hit_count_generic_relation",
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="decks")

    modified_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.owner.username} - {self.name}"

    def get_absolute_url(self):
        return reverse("deck-detail", kwargs={"pk": self.pk})

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

    def get_absolute_url(self):
        return reverse(
            "private-url-deck-detail", kwargs={"pk": self.deck.pk, "code": self.code}
        )

    class Meta:
        ordering = ["-created_at"]


class Comment(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    deck = models.ForeignKey(Deck, on_delete=models.CASCADE, related_name="comments")
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


class FavoriteCard(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favorite_cards",
    )
    card = models.ForeignKey(
        Card, on_delete=models.CASCADE, related_name="favorited_by"
    )

    def __str__(self) -> str:
        return f"{self.user.username} favorited '{self.card.reference}'"

    class Meta:
        unique_together = ("user", "card")


class DeckCopy(models.Model):
    target_deck = models.OneToOneField(
        Deck, on_delete=models.CASCADE, related_name="copies_from"
    )
    source_deck = models.ForeignKey(
        Deck, on_delete=models.CASCADE, null=True, blank=True, related_name="copies_to"
    )
    source_tournament_deck = models.ForeignKey(
        "recommender.TournamentDeck", on_delete=models.CASCADE, null=True, blank=True
    )


class CardPrice(models.Model):
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name="prices")
    price = models.PositiveIntegerField(null=True)
    count = models.PositiveIntegerField(default=1)
    date = models.DateField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["card", "date"], name="unique_card_date_price"
            )
        ]
