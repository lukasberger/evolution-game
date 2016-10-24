from unittest import TestCase

from .feeding_outcome import FeedingOutcome, VegetarianFeeding, CarnivoreFeeding, FatTissueFeeding, NoFeeding, CannotFeed
from ..common.trait import Trait
from ..common.species import Species
from ..dealer.dealer import Dealer
from ..player.player import Player


class FeedingOutcomeTestCase(TestCase):

    def test_serialize_deserialize(self):

        cases = [
            (NoFeeding, False, NoFeeding()),
            (VegetarianFeeding, 1, VegetarianFeeding(1)),
            (FatTissueFeeding, [2, 2], FatTissueFeeding(2, 2)),
            (CarnivoreFeeding, [0, 1, 2], CarnivoreFeeding(0, 1, 2)),
        ]

        for feeding_type, value, expected in cases:
            deserialized = FeedingOutcome.deserialize(value)
            self.assertEqual(deserialized, expected)
            self.assertEqual(deserialized.serialize(), value)

        other_values = [None, "string"]
        for other_value in other_values:
            deserialized_other = FeedingOutcome.deserialize(other_value)
            self.assertEqual(deserialized_other, CannotFeed())

    def test_validate_cannot_feed(self):
        dealer = Dealer()
        self.assertTrue(CannotFeed().validate(dealer))

    def test_validate_no_feeding(self):
        dealer = Dealer()
        self.assertTrue(NoFeeding().validate(dealer))

    def test_validate_feed_vegetarian(self):

        dealer = Dealer(players=[
            Player(1, species=[
                Species(food=0, population=1),
                Species(food=0, population=2),
                Species(food=2, population=2),
            ])
        ])
        self.assertTrue(VegetarianFeeding(0).validate(dealer))
        self.assertTrue(VegetarianFeeding(1).validate(dealer))
        self.assertFalse(VegetarianFeeding(2).validate(dealer))

    def test_validate_feed_fat_tissue(self):

        dealer = Dealer(
            players=[
                Player(1, species=[
                    Species(body=1, traits=[Trait.FAT_TISSUE], fat_food=0),
                    Species(body=4, traits=[Trait.FAT_TISSUE], fat_food=4),
                    Species(body=5, traits=[Trait.FAT_TISSUE], fat_food=0),
                ])
            ],
            watering_hole=4
        )

        self.assertTrue(FatTissueFeeding(0, 1).validate(dealer))
        self.assertTrue(FatTissueFeeding(2, 1).validate(dealer))
        self.assertTrue(FatTissueFeeding(2, 2).validate(dealer))
        self.assertTrue(FatTissueFeeding(2, 3).validate(dealer))
        self.assertTrue(FatTissueFeeding(2, 4).validate(dealer))
        self.assertFalse(FatTissueFeeding(1, 1).validate(dealer))
        self.assertFalse(FatTissueFeeding(2, 5).validate(dealer))
        self.assertFalse(FatTissueFeeding(2, 6).validate(dealer))
