from argparse import ArgumentParser
from collections import defaultdict
from datetime import datetime
from enum import Enum
from http import HTTPStatus
import pickle
import re
from typing import Any

from django.core.management.base import CommandError
from lightgbm import LGBMClassifier
import numpy as np
import pandas as pd
import requests
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.multioutput import MultiOutputClassifier
from xgboost import XGBClassifier

from config.commands import BaseCommand
from config.utils import get_user_agent
from decks.deck_utils import card_code_from_reference
from decks.models import Card
from recommender.model_utils import RecommenderHelper
from recommender.models import Tournament, TournamentDeck, TrainedModel


API_ENDPOINT_LIST_TOURNAMENTS = "https://39cards.com/api/tournaments"
API_ENDPOINT_FETCH_TOURNAMENT = "https://39cards.com/api/tournament/{id}"
HEADERS = {"User-Agent": get_user_agent("Recommender")}


class ModelType(str, Enum):
    LR = "logistic regression"
    LR_TUNED = "logistic regression tuned"
    RANDOM_FOREST = "random forest"
    RANDOM_FOREST_TUNED = "random forest tuned"
    LIGHT_GBM = "light gbm"
    LIGHT_GBM_TUNED = "light gbm tuned"
    XGBOOST = "xgboost"
    XGBOOST_TUNED = "xgboost tuned"


class Command(BaseCommand):
    version = "1.0.0"

    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument("--refresh-data", action="store_true")
        parser.add_argument("--faction", action="store")
        parser.add_argument("model", choices=[model.name.lower() for model in ModelType])

    def handle(self, *args: Any, **options: Any) -> None:

        model_type = ModelType[options["model"].upper()]

        # Optionally, refresh the data used to generate the models
        if options["refresh_data"]:
            self.fetch_tournaments()

        RecommenderHelper.build_card_pool()

        if options["faction"]:
            factions = [Card.Faction(options["faction"])]
        else:
            factions = RecommenderHelper.FACTIONS
        for faction in factions:
            self.create_model(model_type, faction)

    def fetch_tournaments(self) -> None:

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

    def fetch_tournament_decks(self, tournament: Tournament) -> None:
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

    def create_model(self, model_type: ModelType, faction: Card.Faction) -> None:

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
        feature_names = RecommenderHelper.get_feature_names(faction)
        x_train = pd.DataFrame(decks_matrix, columns=feature_names)
        y_train = (decks_matrix > 0).astype(int)

        if model_type == ModelType.LR:
            base_model = OneVsRestClassifier(
                LogisticRegression(
                    max_iter=1000,
                    solver="saga",
                    penalty="l1",
                    class_weight="balanced",
                    C=0.1,
                )
            )
        elif model_type == ModelType.LR_TUNED:
            base_model = OneVsRestClassifier(
                LogisticRegression(
                    max_iter=2000,
                    solver="saga",
                    penalty="elasticnet",
                    l1_ratio=0.5,
                    class_weight="balanced",
                    C=0.5,
                )
            )
        elif model_type == ModelType.RANDOM_FOREST:
            base_model = RandomForestClassifier(
                n_estimators=100,
                n_jobs=-1,
                class_weight="balanced",
                random_state=42,
            )
        elif model_type == ModelType.RANDOM_FOREST_TUNED:
            base_model = RandomForestClassifier(
                n_estimators=300,
                max_depth=20,
                min_samples_leaf=2,
                n_jobs=-1,
                class_weight="balanced_subsample",
                random_state=42,
            )
        elif model_type == ModelType.LIGHT_GBM:
            base_model = LGBMClassifier(
                objective="binary",
                n_estimators=100,
                class_weight="balanced",
                n_jobs=-1,
                random_state=42,
                verbosity=-1
            )
        elif model_type == ModelType.LIGHT_GBM_TUNED:
            base_model = LGBMClassifier(
                objective="binary",
                n_estimators=300,
                learning_rate=0.05,
                num_leaves=31,
                min_child_samples=10,
                class_weight="balanced",
                subsample=0.8,
                colsample_bytree=0.8,
                n_jobs=-1,
                random_state=42,
                verbosity=-1
            )
        elif model_type == ModelType.XGBOOST:
            base_model = XGBClassifier(
                objective="binary:logistic",
                eval_metric="logloss",
                base_score=0.5,
                n_estimators=100,
                learning_rate=0.1,
                n_jobs=-1,
            )
        elif model_type == ModelType.XGBOOST_TUNED:
            base_model = XGBClassifier(
                objective="binary:logistic",
                eval_metric="logloss",
                base_score=0.01,
                n_estimators=300,
                learning_rate=0.05,
                max_depth=6,
                subsample=0.8,
                colsample_bytree=0.8,
                reg_alpha=0.1,
                reg_lambda=1.0,
                n_jobs=-1
            )
        else:
            raise CommandError(f"Unsupported model type: {model_type}")

        model = MultiOutputClassifier(base_model)
        model.fit(x_train, y_train)

        TrainedModel.objects.filter(faction=faction).update(active=False)
        TrainedModel.objects.create(
            faction=faction,
            model_data=pickle.dumps(model),
            active=True,
            period_start=min(deck.tournament.date for deck in decks),
            period_end=max(deck.tournament.date for deck in decks),
            model=model_type.value,
        )
