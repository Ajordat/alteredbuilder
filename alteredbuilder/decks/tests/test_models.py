from django.contrib.auth.models import User
from django.test import TestCase

from decks.models import Card, Character, Deck, Hero, Permanent, Spell


class DecksViewsTestCase(TestCase):
    """Test case focusing on the Models."""

    TEST_USER = "test_user"
    HERO_REFERENCE = "ALT_CORE_B_AX_01_C"
    PROMO_HERO_REFERENCE = "ALT_CORE_P_AX_01_C"
    CHARACTER_REFERENCE = "ALT_CORE_B_YZ_08_C"
    OOF_CHARACTER_REFERENCE = "ALT_CORE_B_YZ_08_R2"
    SPELL_REFERENCE = "ALT_CORE_B_YZ_26_R2"
    PERMANENT_REFERENCE = "ALT_CORE_B_LY_30_R2"
    DECK_NAME = "deck name"

    @classmethod
    def setUpTestData(cls):
        """Create the database data for this test.

        Specifically, it creates:
        * 2 User
        * 2 Hero
        * 2 Character
        * 1 Spell
        * 1 Permanent
        * 1 Deck
        """
        cls.user = User.objects.create_user(username=cls.TEST_USER)
        hero = Hero.objects.create(
            reference=cls.HERO_REFERENCE,
            name="Sierra & Oddball",
            faction=Card.Faction.AXIOM,
            type=Card.Type.HERO,
            rarity=Card.Rarity.COMMON,
        )
        Hero.objects.create(
            reference=cls.PROMO_HERO_REFERENCE,
            name="Sierra & Oddball",
            faction=Card.Faction.AXIOM,
            type=Card.Type.HERO,
            rarity=Card.Rarity.COMMON,
        )
        Character.objects.create(
            reference=cls.CHARACTER_REFERENCE,
            name="Yzmir Stargazer",
            faction=Card.Faction.YZMIR,
            type=Card.Type.CHARACTER,
            rarity=Card.Rarity.COMMON,
            main_cost=2,
            recall_cost=1,
            forest_power=1,
            mountain_power=2,
            ocean_power=1,
        )
        Character.objects.create(
            reference=cls.OOF_CHARACTER_REFERENCE,
            name="Yzmir Stargazer",
            faction=Card.Faction.AXIOM,
            type=Card.Type.CHARACTER,
            rarity=Card.Rarity.RARE,
            main_cost=1,
            recall_cost=1,
            forest_power=1,
            mountain_power=2,
            ocean_power=1,
        )
        Spell.objects.create(
            reference=cls.SPELL_REFERENCE,
            name="Kraken's Wrath",
            faction=Card.Faction.AXIOM,
            type=Card.Type.SPELL,
            rarity=Card.Rarity.RARE,
            main_cost=5,
            recall_cost=5,
        )
        Permanent.objects.create(
            reference=cls.PERMANENT_REFERENCE,
            name="The Ouroboros, Lyra Bastion",
            faction=Card.Faction.AXIOM,
            type=Card.Type.PERMANENT,
            rarity=Card.Rarity.RARE,
            main_cost=3,
            recall_cost=3,
        )
        Deck.objects.create(
            owner=cls.user, name=cls.DECK_NAME, hero=hero, is_public=True
        )

    def test_to_string(self):
        """Test the string representations of all models."""
        hero = Hero.objects.get(reference=self.HERO_REFERENCE)
        character = Character.objects.get(reference=self.CHARACTER_REFERENCE)
        spell = Spell.objects.get(reference=self.SPELL_REFERENCE)
        permanent = Permanent.objects.get(reference=self.PERMANENT_REFERENCE)
        deck = Deck.objects.get(name=self.DECK_NAME)

        self.assertEqual(str(hero), f"{hero.reference} - {hero.name}")
        self.assertEqual(
            str(character),
            f"[{character.faction}] - {character.name} ({character.rarity})",
        )
        self.assertEqual(
            str(spell), f"[{spell.faction}] - {spell.name} ({spell.rarity})"
        )
        self.assertEqual(
            str(permanent),
            f"[{permanent.faction}] - {permanent.name} ({permanent.rarity})",
        )
        self.assertEqual(str(deck), f"{deck.owner.username} - {deck.name}")

    def test_hero_promo(self):
        """Test if the Hero objects correctly identify whether they're a promo card."""
        hero = Hero.objects.get(reference=self.HERO_REFERENCE)
        promo_hero = Hero.objects.get(reference=self.PROMO_HERO_REFERENCE)

        self.assertFalse(hero.is_promo())
        self.assertTrue(promo_hero.is_promo())

    def test_character_oof(self):
        """Test if the Character objects correctly identify whether they're out of
        their original faction or not.
        """
        character = Character.objects.get(reference=self.CHARACTER_REFERENCE)
        oof_character = Character.objects.get(reference=self.OOF_CHARACTER_REFERENCE)

        self.assertFalse(character.is_oof())
        self.assertTrue(oof_character.is_oof())
