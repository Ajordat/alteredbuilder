from collections import defaultdict
from datetime import datetime
from http import HTTPStatus
import pickle
import re
from typing import Any

from django.core.management.base import CommandError
import numpy as np
import requests
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.multioutput import MultiOutputClassifier

from config.commands import BaseCommand
from config.utils import get_user_agent
from decks.deck_utils import card_code_from_reference
from decks.models import Card
from recommender.model_utils import RecommenderHelper
from recommender.models import Tournament, TournamentDeck, TrainedModel


API_ENDPOINT_LIST_TOURNAMENTS = "https://39cards.com/api/tournaments"
API_ENDPOINT_FETCH_TOURNAMENT = "https://39cards.com/api/tournament/{id}"
HEADERS = {"User-Agent": get_user_agent("Recommender")}


class Command(BaseCommand):
    version = "0.1.0"

    def add_arguments(self, parser):
        parser.add_argument("--refresh-data", action="store_true")

    def handle(self, *args: Any, **options: Any) -> None:

        # Optionally, refresh the data used to generate the models
        if options["refresh_data"]:
            self.fetch_tournaments()

        RecommenderHelper.build_card_pool()

        for faction in RecommenderHelper.FACTIONS:
            self.create_model(faction)

    def fetch_tournaments(self):

        response = requests.get(API_ENDPOINT_LIST_TOURNAMENTS, headers=HEADERS)
        if response.status_code != HTTPStatus.OK:
            raise CommandError(
                f"Unable to retrieve tournaments: {response.status_code}"
            )

        tournaments = response.json()

        for t in tournaments:
            startDatetime = datetime.fromisoformat(t["startDate"])
            tournament, created = Tournament.objects.update_or_create(
                remote_id=t["id"],
                defaults={
                    "name": t["name"],
                    "player_count": t["numberOfPlayers"],
                    "date": startDatetime.date(),
                    "location": t["location"],
                },
            )
            if created:
                self.fetch_tournament_decks(tournament)

    def fetch_tournament_decks(self, tournament: Tournament):
        response = requests.get(
            API_ENDPOINT_FETCH_TOURNAMENT.format(id=tournament.remote_id),
            headers=HEADERS,
        )
        if response.status_code != HTTPStatus.OK:
            raise CommandError(
                f"Unable to fetch tournament {tournament.remote_id}: {response.status_code}"
            )
        else:
            self.stdout.write(f"Retrieving data from tournament {tournament.remote_id}")

        tournament_data = response.json()

        for d in tournament_data["topFinishers"]:
            if "deckList" not in d["deck"]:
                continue
            card_map = defaultdict(int)
            hero_reference: str = d["deck"]["hero"]
            try:
                card: dict[str, str]
                for card in d["deck"]["deckList"]:
                    card_map[card_code_from_reference(card["ref"])] += int(card["n"])
                del card_map[card_code_from_reference(hero_reference)]

            except KeyError as e:
                self.stderr.write(d)
                raise e

            try:
                if "rank" in d["finalRank"]:
                    placement = d["finalRank"]["rank"]
                else:
                    placement = int(
                        re.search(r"^\d+", d["finalRank"]["bracket"]).group()
                    )
                TournamentDeck.objects.update_or_create(
                    remote_id=d["id"],
                    tournament=tournament,
                    defaults={
                        "player": d["name"],
                        "placement": placement,
                        "hero": Card.objects.get(reference=hero_reference),
                        "cards": card_map,
                    },
                )
            except (KeyError, TypeError) as e:
                self.stderr.write(d)
                raise e

    def create_model(self, faction):

        # Generate a matrix of decks and their cards
        decks = [deck for deck in TournamentDeck.objects.filter(hero__faction=faction)]
        if len(decks) == 0:
            raise CommandError(f"No decks found for {faction}")
        decks_matrix = np.zeros(
            (len(decks), RecommenderHelper.get_vector_size(faction)), dtype=np.int8
        )
        try:
            for deck_index, deck in enumerate(decks):
                deck_vector = RecommenderHelper.generate_vector_for_deck(deck)
                decks_matrix[deck_index] = deck_vector
        except KeyError as e:
            raise CommandError(
                f"Failed to find card family {e} in card pool for faction {Card.Faction(faction).name}"
            )

        # Train the model
        x_train = decks_matrix.copy()
        y_train = (decks_matrix > 0).astype(int)

        model = MultiOutputClassifier(
            OneVsRestClassifier(
                LogisticRegression(
                    max_iter=1000,
                    solver="saga",
                    penalty="l1",
                    class_weight="balanced",
                    C=0.1,
                )
            )
        )
        model.fit(x_train, y_train)

        TrainedModel.objects.filter(faction=faction).update(active=False)
        TrainedModel.objects.create(
            faction=faction,
            model_data=pickle.dumps(model),
            active=True,
            period_start=min(deck.tournament.date for deck in decks),
            period_end=max(deck.tournament.date for deck in decks),
            model="logistic regression",
        )
