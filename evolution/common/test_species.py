import unittest

from .species import Species
from .trait import Trait, HARD_SHELL_THRESHOLD


class TestSpeciesSerialize(unittest.TestCase):

    def test_serialize_deserialize(self):
        species = Species()
        expected = [['food', 0], ['body', 0], ['population', 1], ['traits', []]]
        self.assertEqual(species.serialize(), expected)
        self.assertEqual(species.deserialize(species.serialize()).serialize(), expected)

        species = Species(traits=[Trait.FAT_TISSUE], body=4, fat_food=4)
        expected = [['food', 0], ['body', 4], ['population', 1], ['traits', ['fat-tissue']], ['fat-food', 4]]
        self.assertEqual(species.serialize(), expected)
        self.assertEqual(species.deserialize(species.serialize()).serialize(), expected)

    def test_add_has_trait(self):
        species = Species(traits=[])

        species.add_trait(Trait.CARNIVORE)
        species.add_trait(Trait.HORNS)
        species.add_trait(Trait.FAT_TISSUE)

        self.assertEqual(len(species.traits), species.MAXIMUM_TRAITS)
        with self.assertRaisesRegex(ValueError, "species can have at most"):
            species.add_trait(Trait.LONG_NECK)

        self.assertTrue(species.has_trait(Trait.CARNIVORE))
        self.assertTrue(species.has_trait(Trait.HORNS))
        self.assertTrue(species.has_trait(Trait.FAT_TISSUE))
        self.assertFalse(species.has_trait(Trait.LONG_NECK))

    def test_attacking_body(self):
        species = Species(body=3, population=4, traits=[])
        self.assertEqual(species.attacking_body, species.body)

        species = Species(body=3, population=4, traits=[Trait.PACK_HUNTING])
        self.assertEqual(species.attacking_body, species.body + species.population)

    def test_is_attackable_warning_call(self):
        attacker = Species(traits=[Trait.CARNIVORE])
        defender = Species()
        warning_species = Species(traits=[Trait.WARNING_CALL])
        other_species = Species()

        self.assertTrue(defender.is_attackable(attacker))
        self.assertFalse(defender.is_attackable(attacker, left=warning_species, right=other_species))
        self.assertFalse(defender.is_attackable(attacker, left=other_species, right=warning_species))

    def test_is_attackable_burrowing(self):
        attacker = Species(traits=[Trait.CARNIVORE])
        defender = Species(food=2, population=2)

        self.assertTrue(defender.is_attackable(attacker))
        defender.add_trait(Trait.BURROWING)
        self.assertFalse(defender.is_attackable(attacker))

    def test_is_attackable_climbing(self):
        attacker = Species(traits=[Trait.CARNIVORE])
        defender = Species()

        self.assertTrue(defender.is_attackable(attacker))
        defender.add_trait(Trait.CLIMBING)
        self.assertFalse(defender.is_attackable(attacker))
        attacker.add_trait(Trait.CLIMBING)
        self.assertTrue(defender.is_attackable(attacker))

    def test_is_attackable_hard_shell_pack_hunting(self):
        attacker = Species(body=1, population=HARD_SHELL_THRESHOLD, traits=[Trait.CARNIVORE])
        defender = Species(body=attacker.body)

        self.assertTrue(defender.is_attackable(attacker))
        defender.add_trait(Trait.HARD_SHELL)
        self.assertFalse(defender.is_attackable(attacker))
        attacker.add_trait(Trait.PACK_HUNTING)
        self.assertTrue(defender.is_attackable(attacker))
        defender.body += 1
        self.assertFalse(defender.is_attackable(attacker))

    def test_is_attackable_herding(self):
        attacker = Species(population=1, traits=[Trait.CARNIVORE])
        defender = Species(population=1)

        self.assertTrue(defender.is_attackable(attacker))
        defender.add_trait(Trait.HERDING)
        self.assertFalse(defender.is_attackable(attacker))
        attacker.population += 1
        self.assertTrue(defender.is_attackable(attacker))

    def test_is_attackable_symbiosis(self):
        attacker = Species(traits=[Trait.CARNIVORE])
        defender = Species(body=1)
        right = Species(body=1)

        self.assertTrue(defender.is_attackable(attacker))
        defender.add_trait(Trait.SYMBIOSIS)
        self.assertTrue(defender.is_attackable(attacker))
        self.assertTrue(defender.is_attackable(attacker, right=right))
        right.body += 1
        self.assertFalse(defender.is_attackable(attacker, right=right))

    def test_is_hungry(self):

        species = Species(food=0, population=4)
        self.assertTrue(species.is_hungry())

        species = Species(food=4, population=4)
        self.assertFalse(species.is_hungry())

    def test_can_store_fat_food(self):

        species = Species(food=0, population=4)
        self.assertFalse(species.can_store_fat_food())

        species = Species(food=0, body=4, population=4, traits=[Trait.FAT_TISSUE], fat_food=0)
        self.assertTrue(species.can_store_fat_food())

        species = Species(food=4, body=4, population=4, traits=[Trait.FAT_TISSUE], fat_food=0)
        self.assertTrue(species.can_store_fat_food())

        species = Species(food=4, body=4, population=4, traits=[Trait.FAT_TISSUE], fat_food=4)
        self.assertFalse(species.can_store_fat_food())

    def test_extinct(self):

        species = Species()
        self.assertFalse(species.is_extinct())
        species = Species(population=Species.MINIMUM_POPULATION)
        self.assertTrue(species.is_extinct())

    def test_feed(self):

        species = Species(food=1, population=1)
        self.assertFalse(species.is_hungry())
        self.assertEqual(species.feed(999), (0, 0, False))
        self.assertEqual(species.food, 1)

        species = Species(food=0, population=7)
        self.assertTrue(species.is_hungry())
        self.assertEqual(species.feed(999), (species.BITE_SIZE, 1, False))
        self.assertEqual(species.food, species.BITE_SIZE)

        species = Species(food=0, population=7, traits=[Trait.FORAGING])
        self.assertTrue(species.is_hungry())
        self.assertEqual(species.feed(999), (species.BITE_SIZE + species.BITE_SIZE, 2, False))
        self.assertEqual(species.food, species.BITE_SIZE + species.BITE_SIZE)

        species = Species(food=1, population=1, traits=[Trait.COOPERATION])
        self.assertFalse(species.is_hungry())
        self.assertEqual(species.feed(999), (0, 0, True))
        self.assertEqual(species.food, 1)

    def test_end_turn(self):

        cases = [
            ("species has no food -> extinct", 0, 1, True, None),
            ("has as much food as population", 4, 4, False, 4),
            ("has as less food than population", 2, 5, False, 2),
        ]

        for msg, food, population, extinct_exp, food_exp in cases:
            species = Species(food=food, population=population)
            self.assertEqual(species.food, food, msg)
            self.assertEqual(species.population, population, msg)
            extinct_act, food_act = species.end_turn()
            self.assertEqual(species.food, Species.MINIMUM_FOOD, msg)
            self.assertEqual(species.population, food, msg)
            self.assertEqual(extinct_act, extinct_exp, msg)
            self.assertEqual(food_act, food_exp, msg)

    def test_display(self):

        species = Species(food=1, population=1, traits=[Trait.COOPERATION])
        species_fat = Species(food=1, population=1, body=3, traits=[Trait.FAT_TISSUE], fat_food=0)
        species_fat_gt_1 = Species(food=1, population=1, body=3, traits=[Trait.FAT_TISSUE], fat_food=1)

        species_expected = {
            Species.DISPLAY_KEY_FOOD: 1,
            Species.DISPLAY_KEY_BODY: 0,
            Species.DISPLAY_KEY_POPULATION: 1,
            Species.DISPLAY_KEY_TRAITS: [trait.value for trait in species.traits]
        }

        species_fat_expected = {
            Species.DISPLAY_KEY_FOOD: 1,
            Species.DISPLAY_KEY_BODY: 3,
            Species.DISPLAY_KEY_POPULATION: 1,
            Species.DISPLAY_KEY_TRAITS: [trait.value for trait in species_fat.traits]
        }

        species_fat_gt_1_expected = {
            Species.DISPLAY_KEY_FOOD: 1,
            Species.DISPLAY_KEY_BODY: 3,
            Species.DISPLAY_KEY_POPULATION: 1,
            Species.DISPLAY_KEY_TRAITS: [trait.value for trait in species_fat_gt_1.traits],
            Species.DISPLAY_KEY_FAT_FOOD: 1
        }

        self.assertEqual(species.display(), species_expected)
        self.assertEqual(species_fat.display(), species_fat_expected)
        self.assertEqual(species_fat_gt_1.display(), species_fat_gt_1_expected)
