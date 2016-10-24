from unittest import TestCase

from .trait import Trait
from .trait_card import TraitCard


class TraitCardTestCase(TestCase):

    def test_ordering(self):

        # t1 < t2;  v1 == v2
        self.assertLess(TraitCard(0, Trait.AMBUSH), TraitCard(0, Trait.CARNIVORE))
        # t1 > t2;  v1 == v2
        self.assertGreater(TraitCard(0, Trait.CARNIVORE), TraitCard(0, Trait.AMBUSH))
        # t1 == t2; v1 == v2
        self.assertEqual(TraitCard(0, Trait.CARNIVORE), TraitCard(0, Trait.CARNIVORE))

        # t1 < t2;  v1 < v2
        self.assertLess(TraitCard(0, Trait.AMBUSH), TraitCard(1, Trait.CARNIVORE))
        # t1 > t2;  v1 < v2
        self.assertGreater(TraitCard(0, Trait.CARNIVORE), TraitCard(1, Trait.AMBUSH))
        # t1 == t2; v1 < v2
        self.assertLess(TraitCard(0, Trait.CARNIVORE), TraitCard(1, Trait.CARNIVORE))

        # t1 < t2;  v1 > v2
        self.assertLess(TraitCard(1, Trait.AMBUSH), TraitCard(0, Trait.CARNIVORE))
        # t1 > t2;  v1 > v2
        self.assertGreater(TraitCard(1, Trait.CARNIVORE), TraitCard(0, Trait.AMBUSH))
        # t1 == t2; v1 > v2
        self.assertGreater(TraitCard(1, Trait.CARNIVORE), TraitCard(0, Trait.CARNIVORE))

    def test_display(self):

        tc1 = TraitCard(-1, Trait.AMBUSH)
        tc2 = TraitCard(-2, Trait.CARNIVORE)

        tc1_expected = {
            TraitCard.DISPLAY_KEY_TRAIT: "ambush",
            TraitCard.DISPLAY_KEY_VALUE: -1
        }

        tc2_expected = {
            TraitCard.DISPLAY_KEY_TRAIT: "carnivore",
            TraitCard.DISPLAY_KEY_VALUE: -2
        }

        self.assertEqual(tc1.display(), tc1_expected)
        self.assertEqual(tc2.display(), tc2_expected)
