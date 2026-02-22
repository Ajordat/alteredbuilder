from collections import OrderedDict
import pickle

from django.db.models import F
import numpy as np
import numpy.typing as npt
import pandas as pd
from sklearn.multioutput import MultiOutputClassifier

from decks.models import Card
from recommender.models import TournamentDeck, TrainedModel


class RecommenderHelper:
    FACTIONS = Card.Faction.as_list()
    HEROES = {
        Card.Faction.AXIOM: ["AX_01_C", "AX_02_C", "AX_03_C", "AX_65_C", "AX_85_C"],
        Card.Faction.BRAVOS: ["BR_01_C", "BR_02_C", "BR_03_C", "BR_65_C"],
        Card.Faction.LYRA: ["LY_01_C", "LY_02_C", "LY_03_C", "LY_65_C"],
        Card.Faction.MUNA: ["MU_01_C", "MU_02_C", "MU_03_C", "MU_65_C", "MU_85_C"],
        Card.Faction.ORDIS: ["OR_01_C", "OR_02_C", "OR_03_C", "OR_65_C", "OR_85_C"],
        Card.Faction.YZMIR: ["YZ_01_C", "YZ_02_C", "YZ_03_C", "YZ_65_C"],
    }
    CARD_POOL = {
        Card.Faction.AXIOM: [],
        Card.Faction.BRAVOS: [],
        Card.Faction.LYRA: [],
        Card.Faction.MUNA: [],
        Card.Faction.ORDIS: [],
        Card.Faction.YZMIR: [],
    }
    SPECIAL_ADDITIONS = {
        Card.Faction.AXIOM: [],
        Card.Faction.BRAVOS: [
            "ALT_BISE_P_BR_64_C",  # Sofia, First Outpost
            "ALT_BISE_P_BR_64_R1",  # Sofia, First Outpost
        ],
        Card.Faction.LYRA: [],
        Card.Faction.MUNA: [
            "ALT_BISE_P_BR_64_R2",  # Sofia, First Outpost
        ],
        Card.Faction.ORDIS: [
            "ALT_ALIZE_P_OR_48_C",  # Kuraokami Unbound
            "ALT_ALIZE_P_OR_48_R1",  # Kuraokami Unbound
        ],
        Card.Faction.YZMIR: [
            "ALT_ALIZE_P_OR_48_R2",  # Kuraokami Unbound
        ],
    }

    @classmethod
    def build_card_pool(cls) -> None:
        if len(cls.CARD_POOL.get(Card.Faction.AXIOM)) > 0:
            return
        for faction in cls.FACTIONS:
            cards = (
                Card.objects.annotate(release_date=F("set__release_date"))
                .filter(
                    faction=faction,
                    rarity__in=[Card.Rarity.COMMON, Card.Rarity.RARE],
                    is_legal=True, is_main_set=True
                )
                .exclude(type=Card.Type.HERO)
                .exclude(is_alt_art=True)
                .exclude(is_promo=True)
                .only("reference", "type")
            )

            exceptions = cls.SPECIAL_ADDITIONS.get(faction, [])
            if len(exceptions) > 0:
                cards = cards.union(
                    Card.objects.annotate(release_date=F("set__release_date"))
                    .filter(reference__in=exceptions)
                    .only("reference", "type")
                )

            cards = cards.order_by("set__release_date", "reference")

            codes = OrderedDict()
            for card in cards:
                family_code = card.get_card_code()
                if family_code not in codes:
                    codes[family_code] = None

                    if card.type == Card.Type.CHARACTER:
                        unique_code = card.get_family_code() + "_U"
                        codes[unique_code] = None

            cls.CARD_POOL[faction] = list(codes.keys())

    @staticmethod
    def load_model(faction: Card.Faction) -> MultiOutputClassifier:
        try:
            trained_model = TrainedModel.objects.get(faction=faction, active=True)
            return pickle.loads(trained_model.model_data)
        except TrainedModel.DoesNotExist:
            return None

    @classmethod
    def generate_vector_for_deck(
        cls,
        deck: TournamentDeck = None,
        faction: Card.Faction = None,
        hero: str = None,
        cards: dict[str, int] = None,
    ) -> npt.NDArray:

        faction = faction if faction else Card.Faction(deck.hero.faction)
        hero = hero if hero else deck.hero.get_card_code()
        cards = cards if cards else deck.cards if deck else {}

        # size = amount_of_heroes + faction_card_pool * card_variants_in_a_faction
        vector = np.zeros(cls.get_vector_size(faction), dtype=np.int8)
        vector[cls.HEROES[faction].index(hero)] = 1

        offset = len(cls.HEROES[faction])

        for card_code, quantity in cards.items():
            try:
                card_index = cls.CARD_POOL[faction].index(card_code)
            except ValueError:
                card_code = f"{card_code[:-1]}{2 if card_code[-1] == '1' else 1}"
                card_index = cls.CARD_POOL[faction].index(card_code)

            vector[offset + card_index] += quantity

        return vector

    @classmethod
    def get_recommended_cards(
        cls,
        model: MultiOutputClassifier,
        deck_vector: npt.NDArray,
        faction: Card.Faction,
        top_n: int,
    ) -> list[str, Card.Rarity]:

        # Reshape the vector to match the input shape (1, n_features)
        deck_vector = deck_vector.reshape(1, -1)
        feature_names = RecommenderHelper.get_feature_names(faction)
        df = pd.DataFrame(deck_vector, columns=feature_names)

        # Predict with the model
        predictions = model.predict_proba(df)

        present_mask = deck_vector[0] > 0
        probas_flat = np.array(
            [
                p[0][1] if isinstance(p[0], (list, np.ndarray)) else p[0]
                for p in predictions
            ]
        )
        probas_flat[present_mask] = 0

        indexes = probas_flat.argsort()[::-1][:top_n]

        cards = []
        offset = len(cls.HEROES[faction])
        for index in indexes:
            if not probas_flat[index]:
                continue
            if index < offset:
                continue
            cards.append(cls.CARD_POOL[faction][index - offset])

        return cards

    @classmethod
    def get_vector_size(cls, faction: Card.Faction) -> int:
        return len(cls.HEROES[faction]) + len(cls.CARD_POOL[faction])

    @classmethod
    def get_feature_names(cls, faction: Card.Faction) -> list[str]:
        return cls.HEROES[faction] + cls.CARD_POOL[faction]
