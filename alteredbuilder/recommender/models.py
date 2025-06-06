from collections import defaultdict

from django.db import models

from decks.models import Card, Deck

EXTERNAL_DECK_URL_39CARDS = "https://39cards.com/tr/{}/p/{}"


# Create your models here.
class Tournament(models.Model):
    remote_id = models.IntegerField(unique=True)
    name = models.CharField()
    player_count = models.IntegerField()
    date = models.DateField()
    location = models.CharField()


class TournamentDeck(models.Model):
    player_id = models.IntegerField()
    player = models.CharField()
    tournament = models.ForeignKey(Tournament, null=True, on_delete=models.CASCADE)
    placement = models.IntegerField()
    hero = models.ForeignKey(Card, blank=False, null=False, on_delete=models.PROTECT)
    cards = models.JSONField()

    def from_deck(
        tournament: Tournament, placement: int, deck: Deck
    ) -> "TournamentDeck":
        t_deck = TournamentDeck(
            player=deck.owner.username,
            tournament=tournament,
            placement=placement,
            hero=deck.hero,
        )
        decklist = deck.cardindeck_set.select_related("card")
        card_map = defaultdict(int)
        for cid in decklist:
            card_code = cid.card.get_card_code()
            card_map[card_code] += cid.quantity
        t_deck.cards = card_map
        return t_deck

    def get_absolute_url(self):
        return EXTERNAL_DECK_URL_39CARDS.format(
            self.tournament.remote_id, self.player_id
        )


class TrainedModel(models.Model):
    faction = models.CharField(max_length=2, choices=Card.Faction)
    model_data = models.BinaryField()
    active = models.BooleanField(default=False)
    model = models.CharField(null=False, blank=False)

    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        permissions = [("can_use_recommender", "Can use deck recommender")]

    def __str__(self) -> str:
        return f"Model for {self.faction} trained from {self.period_start} to {self.period_end}"
