import pickle

import numpy as np
import numpy.typing as npt
from sklearn.base import ClassifierMixin

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
    def build_card_pool(cls):
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
            for card in cards:
                family_code = card.get_family_code()
                if family_code not in cls.CARD_POOL[faction]:
                    cls.CARD_POOL[faction].append(family_code)

            hero_pool_length = len(cls.HEROES[faction])
            card_pool_length = len(cls.CARD_POOL[faction])
            cls.OFFSETS[faction] = [
                0,  # heroes
                hero_pool_length,  # commons
                hero_pool_length + card_pool_length,  # rares
                hero_pool_length + card_pool_length * 2,  # uniques
            ]

    @staticmethod
    def load_model(faction: Card.Faction) -> ClassifierMixin:
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
    ):
        faction = faction if faction else Card.Faction(deck.hero.faction)
        hero = hero if hero else deck.hero.get_card_code()
        cards = cards if cards else deck.cards if deck else {}

        # size = amount_of_heroes + faction_card_pool * card_variants_in_a_faction
        vector = np.zeros(cls.get_vector_size(faction), dtype=np.int8)
        vector[cls.HEROES[faction].index(hero)] = 1

        family_counts = {
            card_family: {
                Card.Rarity.COMMON: 0,
                Card.Rarity.RARE: 0,
                Card.Rarity.UNIQUE: 0,
            }
            for card_family in cls.CARD_POOL[faction]
        }

        for card_code, quantity in cards.items():
            family_code, rarity = card_code.rsplit("_", 1)
            rarity = Card.Rarity(rarity[0])
            family_counts[family_code][rarity] += quantity

        offset_common = len(cls.HEROES[faction])
        offset_rare = offset_common + len(cls.CARD_POOL[faction])
        offset_unique = offset_rare + len(cls.CARD_POOL[faction])

        for i, family in enumerate(cls.CARD_POOL[faction]):
            vector[offset_common + i] = family_counts[family][Card.Rarity.COMMON]
            vector[offset_rare + i] = family_counts[family][Card.Rarity.RARE]
            vector[offset_unique + i] = family_counts[family][Card.Rarity.UNIQUE]

        return vector

    @classmethod
    def get_recommended_cards(
        cls, model: ClassifierMixin, deck_vector: npt.NDArray, faction: Card.Faction
    ):

        # Reshape the vector to match the input shape (1, n_features)
        deck_vector = deck_vector.reshape(1, -1)

        # Predict with the model
        predictions = model.predict(deck_vector)

        # Collect recommended cards (indices where prediction is 1)
        indexes = [index for index, value in enumerate(predictions[0]) if value == 1]

        card_pool_size = len(cls.CARD_POOL[faction])

        offsets = iter(cls.OFFSETS[faction][1:])
        rarities = iter(Card.Rarity.as_list())

        cards = []
        offset = next(offsets)
        rarity = next(rarities)
        for index in indexes:
            while index >= offset + card_pool_size:
                offset = next(offsets)
                rarity = next(rarities)
            cards.append((cls.CARD_POOL[faction][index - offset], rarity))

        return cards

    @classmethod
    def get_vector_size(cls, faction):
        return len(cls.HEROES[faction]) + len(cls.CARD_POOL[faction]) * 3
