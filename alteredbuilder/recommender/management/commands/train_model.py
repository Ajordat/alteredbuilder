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

from recommender.model_utils import ModelHelper
from decks.models import Card
from config.commands import BaseCommand
from recommender.models import Tournament, TournamentDeck, TrainedModel


API_ENDPOINT_LIST_TOURNAMENTS = "https://39cards.com/api/tournaments"
API_ENDPOINT_FETCH_TOURNAMENT = "https://39cards.com/api/tournament/{id}"
HEADERS = {
    "User-Agent": "Ajordat-Recommender/1.0 (Altered TCG Builder; Model Training; https://altered.ajordat.com; Discord: ajordat)"
}


class Command(BaseCommand):
    version = "0.1.0"

    def add_arguments(self, parser):
        parser.add_argument("--refresh-data", action="store_true")

    def handle(self, *args: Any, **options: Any) -> None:

        # Optionally, refresh the data used to generate the models
        if options["refresh_data"]:
            self.fetch_tournaments()

        ModelHelper.build_card_pool()

        for faction in ModelHelper.FACTIONS:
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
                    card_code = "_".join(card["ref"].split("_")[3:6])
                    card_map[card_code] += int(card["n"])
                del card_map["_".join(hero_reference.split("_")[3:6])]

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
        decks = TournamentDeck.objects.filter(hero__faction=faction)
        decks_matrix = np.zeros(
            (len(decks), ModelHelper.get_vector_size(faction)), dtype=np.int8
        )
        for deck_index, deck in enumerate(decks):
            deck_vector = ModelHelper.generate_vector_for_deck(deck)
            decks_matrix[deck_index] = deck_vector

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
        )
