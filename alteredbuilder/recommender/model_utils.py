import pickle

import numpy as np
import numpy.typing as npt
from sklearn.multioutput import MultiOutputClassifier

from decks.models import Card
from recommender.models import TournamentDeck, TrainedModel


class RecommenderHelper:
    FACTIONS = Card.Faction.as_list()
    HEROES = {
        Card.Faction.AXIOM: ["AX_01_C", "AX_02_C", "AX_03_C"],
        Card.Faction.BRAVOS: ["BR_01_C", "BR_02_C", "BR_03_C"],
        Card.Faction.LYRA: ["LY_01_C", "LY_02_C", "LY_03_C"],
        Card.Faction.MUNA: ["MU_01_C", "MU_02_C", "MU_03_C"],
        Card.Faction.ORDIS: ["OR_01_C", "OR_02_C", "OR_03_C"],
        Card.Faction.YZMIR: ["YZ_01_C", "YZ_02_C", "YZ_03_C"],
    }
    CARD_POOL = {
        Card.Faction.AXIOM: [],
        Card.Faction.BRAVOS: [],
        Card.Faction.LYRA: [],
        Card.Faction.MUNA: [],
        Card.Faction.ORDIS: [],
        Card.Faction.YZMIR: [],
    }
    OFFSETS = {
        Card.Faction.AXIOM: [],
        Card.Faction.BRAVOS: [],
        Card.Faction.LYRA: [],
        Card.Faction.MUNA: [],
        Card.Faction.ORDIS: [],
        Card.Faction.YZMIR: [],
    }

    @classmethod
    def build_card_pool(cls) -> None:
        if len(cls.CARD_POOL.get(Card.Faction.AXIOM)) > 0:
            return
        for faction in cls.FACTIONS:
            cards = (
                Card.objects.filter(
                    faction=faction, rarity__in=[Card.Rarity.COMMON, Card.Rarity.RARE]
                )
                .exclude(type=Card.Type.HERO)
                .order_by("set__release_date", "reference")
            )

            cls.CARD_POOL[faction] = []
            for card in cards:
                family_code = card.get_card_code()
                cls.CARD_POOL[faction].append(family_code)
                if card.type == Card.Type.CHARACTER:
                    unique_code = card.get_family_code() + "_U"
                    if unique_code not in cls.CARD_POOL[faction]:
                        cls.CARD_POOL[faction].append(unique_code)

            # hero_pool_length = len(cls.HEROES[faction])
            # card_pool_length = len(cls.CARD_POOL[faction])
            # cls.OFFSETS[faction] = [
            #     0,  # heroes
            #     hero_pool_length,  # commons
            #     hero_pool_length + card_pool_length,  # rares
            #     hero_pool_length + card_pool_length * 2,  # uniques
            # ]

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
    ) -> list[str, Card.Rarity]:

        # Reshape the vector to match the input shape (1, n_features)
        deck_vector = deck_vector.reshape(1, -1)

        # Predict with the model
        predictions = model.predict(deck_vector)

        # Collect recommended cards (indices where prediction is 1)
        indexes = [index for index, value in enumerate(predictions[0]) if value == 1]

        cards = []
        offset = len(cls.HEROES[faction])
        for index in indexes:
            if index < offset:
                continue
            cards.append(cls.CARD_POOL[faction][index - offset])

        return cards

    @classmethod
    def get_vector_size(cls, faction: Card.Faction) -> int:
        return len(cls.HEROES[faction]) + len(cls.CARD_POOL[faction])
