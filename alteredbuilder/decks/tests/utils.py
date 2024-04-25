from random import randint

from decks.models import Card, Character, Hero, Permanent, Spell


def get_id():
    _id = 1
    while True:
        yield _id
        _id += 1


get_id = get_id()


def generate_card(faction, card_type, rarity):
    card_id = next(get_id)
    data = {
        "reference": f"ALT_CORE_B_{faction.value}_{card_id}_{rarity.value}",
        "name": f"{card_type.value} card {card_id}",
        "faction": faction,
        "type": card_type,
        "rarity": rarity,
    }
    cost = {
        "main_cost": randint(1, 10),
        "recall_cost": randint(1, 10),
    }
    match card_type:
        case Card.Type.HERO:
            card = Hero.objects.create(**data)
        case Card.Type.CHARACTER:
            card = Character.objects.create(
                **data,
                **cost,
                forest_power=randint(0, 10),
                mountain_power=randint(0, 10),
                ocean_power=randint(0, 10),
            )
        case Card.Type.SPELL:
            card = Spell.objects.create(**data, **cost)
        case Card.Type.PERMANENT:
            card = Permanent.objects.create(**data, **cost)

    return card
