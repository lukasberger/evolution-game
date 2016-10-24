from unittest import TestCase

from .base_player import BasePlayer

from ..common.trait import Trait
from ..common.species import Species
from ..common.feeding_outcome import VegetarianFeeding, FatTissueFeeding, CarnivoreFeeding


class GetPossibleFeedingsTestCase(TestCase):

    def test_get_possible_vegetarian_feedings(self):

        player = BasePlayer(species=[])
        self.assertEqual(player.get_possible_vegetarian_feedings(), [])

        player = BasePlayer(species=[
            Species(food=0, population=1, traits=[]),  # hungry
            Species(food=1, population=1, traits=[]),  # full
            Species(food=1, population=2, traits=[]),  # hungry
            Species(food=0, population=2, traits=[Trait.CARNIVORE]),  # hungry but carnivore
            Species(food=2, population=2, traits=[Trait.FAT_TISSUE], fat_food=0),  # can store fat, but not hungry
        ])

        expected = [VegetarianFeeding(x) for x in [0, 2]]
        self.assertEqual(player.get_possible_vegetarian_feedings(), expected)

    def test_get_possible_fat_tissue_feedings(self):

        player = BasePlayer(species=[])
        self.assertEqual(player.get_possible_fat_tissue_feedings(1), [])

        player = BasePlayer(species=[
            Species(food=0, population=1, traits=[]),  # not fat tissue
            Species(food=2, population=2, body=2, traits=[Trait.FAT_TISSUE], fat_food=0),  # can store 2 tokens
            Species(food=2, population=5, body=5, traits=[Trait.FAT_TISSUE], fat_food=0),  # can store 5 tokens
        ])

        expected_2 = [
            FatTissueFeeding(1, 2),  # can store 2, 2 available
            FatTissueFeeding(2, 2),  # can store 5, but only 2 available
        ]

        self.assertEqual(player.get_possible_fat_tissue_feedings(2), expected_2)

        expected_5 = [
            FatTissueFeeding(1, 2),  # can store 2, 5 available
            FatTissueFeeding(2, 5),  # can store 5, 5 available
        ]

        self.assertEqual(player.get_possible_fat_tissue_feedings(5), expected_5)

        expected_2_suboptimal = [
            FatTissueFeeding(1, 1),
            FatTissueFeeding(1, 2),
            FatTissueFeeding(2, 1),
            FatTissueFeeding(2, 2),
        ]

        self.assertEqual(player.get_possible_fat_tissue_feedings(2, include_suboptimal=True), expected_2_suboptimal)

    def test_get_possible_carnivore_feedings_empty(self):

        player = BasePlayer(species=[])
        self.assertEqual(player.get_possible_carnivore_feedings([]), [])

    def test_get_possible_carnivore_feedings_no_species(self):

        players = [
            BasePlayer(species=[Species()]),
            BasePlayer(species=[Species()]),
        ]

        player = BasePlayer(species=[])
        self.assertEqual(player.get_possible_carnivore_feedings(players), [])

    def test_get_possible_carnivore_feedings_some_targets(self):

        player = BasePlayer(species=[
            Species(food=0, population=4, traits=[Trait.CARNIVORE]),
            Species(food=0, population=1, traits=[]),  # not a carnivore
        ])

        players = [
            BasePlayer(species=[Species()]),
            BasePlayer(species=[Species()]),
        ]

        expected = [
            CarnivoreFeeding(0, 0, 0),
            CarnivoreFeeding(0, 1, 0),
        ]
        self.assertEqual(player.get_possible_carnivore_feedings(players), expected)

    def test_get_possible_carnivore_feedings_some_defended(self):

        player = BasePlayer(species=[
            Species(food=0, population=4, traits=[Trait.CARNIVORE]),
            Species(food=0, population=1, traits=[]),  # not a carnivore
        ])

        players = [
            BasePlayer(species=[Species(), Species(traits=[Trait.WARNING_CALL]), Species()]),
            BasePlayer(species=[Species(traits=[Trait.CLIMBING])]),
        ]

        expected = [
            CarnivoreFeeding(0, 0, 1),
        ]
        self.assertEqual(player.get_possible_carnivore_feedings(players), expected)
