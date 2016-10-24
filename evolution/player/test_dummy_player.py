from unittest import TestCase

from .dummy_player import DummyPlayer
from ..common.trait import Trait
from ..common.trait_card import TraitCard
from ..common.species import Species
from ..common.feeding_outcome import FatTissueFeeding, VegetarianFeeding, CarnivoreFeeding, NoFeeding, CannotFeed


class TestDummyPlayer(TestCase):

    def test_start_and_update_state(self):

        player_before = DummyPlayer(idx=1, species=[], cards=[], bag=0)
        player_after = DummyPlayer(idx=1,
                                   species=[Species(food=1, body=2, population=1,
                                                    traits=[Trait.FAT_TISSUE], fat_food=1)],
                                   cards=[TraitCard(Trait.CARNIVORE, 0)],
                                   bag=3)

        watering_hole = 4
        state = [
                 [[["food", 1], ["body", 2], ["population", 1], ["traits", ["fat-tissue"]], ["fat-food", 1]]],
                 3,
                 [[0, "carnivore"]]
                ]

        self.assertEqual(player_before.serialize(), DummyPlayer(idx=1, species=[], cards=[], bag=0).serialize())
        player_before.update_state(state)
        self.assertEqual(player_before.serialize(), player_after.serialize())

        player_before = DummyPlayer(idx=1, species=[], cards=[], bag=0)
        player_after = DummyPlayer(idx=1,
                                   species=[Species(food=1, body=2, population=1,
                                                    traits=[Trait.FAT_TISSUE], fat_food=1)],
                                   cards=[TraitCard(Trait.CARNIVORE, 0)],
                                   bag=3)

        self.assertEqual(player_before.serialize(), DummyPlayer(idx=1, species=[], cards=[], bag=0).serialize())
        player_before.start(watering_hole, state)
        self.assertEqual(player_before.serialize(), player_after.serialize())

    def test_feed_next(self):

        #Fat Tissue
        player_before = DummyPlayer(idx=1, species=[], cards=[], bag=0)
        fat_state = [
            [[["food", 1], ["body", 2], ["population", 1], ["traits", ["fat-tissue"]], ["fat-food", 1]]],
            3,
            [[0, "carnivore"]]
        ]
        self.assertEqual(player_before.feed_next(fat_state, [], 4), FatTissueFeeding(0, 1).serialize())

        #Vegetarian
        player_before = DummyPlayer(idx=1, species=[], cards=[], bag=0)
        veg_post_fat_state = [
            [[["food", 1], ["body", 2], ["population", 1], ["traits", ["fat-tissue"]], ["fat-food", 2]],
             [["food", 1], ["body", 2], ["population", 2], ["traits", ["long-neck"]]]],
            3,
            [[0, "carnivore"]]
        ]
        self.assertEqual(player_before.feed_next(veg_post_fat_state, [], 4), VegetarianFeeding(1).serialize())

        #Carnivore
        player_before = DummyPlayer(idx=1, species=[], cards=[], bag=0)
        car_post_veg_post_fat_state = [
            [[["food", 1], ["body", 2], ["population", 1], ["traits", ["fat-tissue"]], ["fat-food", 2]],
             [["food", 2], ["body", 2], ["population", 2], ["traits", ["long-neck"]]],
             [["food", 1], ["body", 2], ["population", 3], ["traits", ["carnivore"]]]],
            3,
            [[0, "carnivore"]]
        ]
        vuln = Species(food=1, body=7, population=1, traits=[Trait.WARNING_CALL]).serialize()
        target = DummyPlayer(idx=2, species=[vuln])
        self.assertEqual(player_before.feed_next(car_post_veg_post_fat_state, [[vuln]], 4),
                         CarnivoreFeeding(2, 0, 0).serialize())

        #Cannot attack
        player_before = DummyPlayer(idx=1, species=[], cards=[], bag=0)
        can_post_car_post_veg_post_fat_state = [
            [[["food", 1], ["body", 2], ["population", 1], ["traits", ["fat-tissue"]], ["fat-food", 2]],
             [["food", 2], ["body", 2], ["population", 2], ["traits", ["long-neck"]]],
             [["food", 1], ["body", 2], ["population", 3], ["traits", ["carnivore"]]]],
            3,
            [[0, "carnivore"]]
        ]
        vuln = Species(food=1, body=7, population=1, traits=[Trait.CLIMBING]).serialize()
        target = DummyPlayer(idx=2, species=[vuln])
        self.assertEqual(player_before.feed_next(can_post_car_post_veg_post_fat_state, [[vuln]], 4),
                         NoFeeding().serialize())

        #Forfeit
        player_before = DummyPlayer(idx=1, species=[], cards=[], bag=0)
        no_post_can_post_car_post_veg_post_fat_state = [
            [[["food", 1], ["body", 2], ["population", 1], ["traits", ["fat-tissue"]], ["fat-food", 2]],
             [["food", 2], ["body", 2], ["population", 2], ["traits", ["long-neck"]]],
             [["food", 3], ["body", 2], ["population", 3], ["traits", ["carnivore"]]]],
            3,
            [[0, "carnivore"]]
        ]
        vuln = Species(food=1, body=7, population=1, traits=[Trait.CLIMBING]).serialize()
        target = DummyPlayer(idx=2, species=[vuln])
        self.assertEqual(player_before.feed_next(no_post_can_post_car_post_veg_post_fat_state, [[vuln]], 4),
                                            CannotFeed().serialize())

    def test_choose(self):

        cases = [
            # 3 cards
            ([TraitCard(0, Trait.CARNIVORE), TraitCard(-1, Trait.CARNIVORE), TraitCard(0, Trait.AMBUSH)],
             [2, [], [], [[1, 0]], []]),

            # 4 cards
            ([TraitCard(0, Trait.CARNIVORE), TraitCard(-1, Trait.CARNIVORE), TraitCard(0, Trait.AMBUSH),
              TraitCard(1, Trait.LONG_NECK)],
             [2, [["population", 0, 3]], [], [[1, 0]], []]),

            # 5 cards
            ([TraitCard(0, Trait.CARNIVORE), TraitCard(-1, Trait.CARNIVORE), TraitCard(0, Trait.AMBUSH),
              TraitCard(1, Trait.LONG_NECK), TraitCard(2, Trait.LONG_NECK)],
             [2, [["population", 0, 3]], [["body", 0, 4]], [[1, 0]], []]),

            # 6 cards
            ([TraitCard(0, Trait.CARNIVORE), TraitCard(-1, Trait.CARNIVORE), TraitCard(0, Trait.AMBUSH),
              TraitCard(1, Trait.LONG_NECK), TraitCard(2, Trait.LONG_NECK), TraitCard(3, Trait.LONG_NECK)],
             [2, [["population", 0, 3]], [["body", 0, 4]], [[1, 0]], [[0, 0, 5]]]),
        ]

        for cards, expected in cases:
            p1 = DummyPlayer(idx=1, species=[], cards=cards)
            self.assertEqual(p1.species, [])
            self.assertEqual(p1.cards, cards)
            self.assertEqual(p1.choose([], []), expected)

    def test_get_max_values(self):
        pass

    def test_species_ordering_key(self):
        pass

    def test_order_species(self):
        pass

    def test_feed_fat_tissue(self):
        # fat_food < body
        hungry_fat_1 = Species(food=1, body=2, population=1, traits=[Trait.FAT_TISSUE], fat_food=1)
        hungry_fat_2 = Species(food=1, body=3, population=1, traits=[Trait.FAT_TISSUE], fat_food=1)
        # 3/4/5 all have same fat need, so we show that ordering by body, then food, then population
        hungry_fat_3 = Species(food=1, body=4, population=1, traits=[Trait.FAT_TISSUE], fat_food=1)
        hungry_fat_4 = Species(food=2, body=4, population=1, traits=[Trait.FAT_TISSUE], fat_food=1)
        hungry_fat_5 = Species(food=2, body=4, population=2, traits=[Trait.FAT_TISSUE], fat_food=1)

        dummy = DummyPlayer(idx=1, species=[hungry_fat_1, hungry_fat_2, hungry_fat_3, hungry_fat_4, hungry_fat_5])
        self.assertEqual(dummy.feed_fat_tissue(dummy.species, 2).serialize(),
                         FatTissueFeeding(4, 2).serialize())

    def test_feed_vegetarian(self):
        # pop > food
        vegetarian_1 = Species(food=1, body=2, population=2, traits=[Trait.LONG_NECK])
        vegetarian_2 = Species(food=1, body=3, population=2, traits=[Trait.LONG_NECK])
        # 3/4/5 all have same food need, so we show that ordering by body, then food, then population
        vegetarian_3 = Species(food=2, body=4, population=3, traits=[Trait.LONG_NECK])
        vegetarian_4 = Species(food=2, body=4, population=3, traits=[Trait.LONG_NECK])
        vegetarian_5 = Species(food=3, body=4, population=5, traits=[Trait.LONG_NECK])

        dummy = DummyPlayer(idx=1, species=[vegetarian_1, vegetarian_2, vegetarian_3, vegetarian_4, vegetarian_5])
        self.assertEqual(dummy.feed_vegetarian(dummy.species).serialize(),
                         VegetarianFeeding(4).serialize())

    def test_feed_carnivore(self):
        carn_1 = Species(food=1, body=2, population=3, traits=[Trait.CARNIVORE])
        carn_2 = Species(food=1, body=7, population=3, traits=[Trait.CARNIVORE])
        vuln_1 = Species(food=1, body=1, population=1, traits=[Trait.WARNING_CALL])
        vuln_2 = Species(food=1, body=7, population=1, traits=[Trait.WARNING_CALL])
        prot = Species(food=1, body=1, population=1, traits=[Trait.LONG_NECK])

        attacker = DummyPlayer(idx=1, species=[carn_1, carn_2])
        defender_1 = DummyPlayer(idx=2, species=[vuln_1, prot])
        defender_2 = DummyPlayer(idx=2, species=[vuln_2, prot])

        self.assertEquals(attacker.feed_carnivore([carn_1, carn_2], [defender_1, defender_2]).serialize(),
                          [1, 1, 0])

    def test_get_largest_attackable_species(self):
        carn = Species(food=1, body=2, population=3, traits=[Trait.CARNIVORE])
        vuln = Species(food=1, body=1, population=1, traits=[Trait.WARNING_CALL])
        prot = Species(food=1, body=1, population=1, traits=[Trait.LONG_NECK])
        attacker = DummyPlayer(idx=1, species=[carn])
        defender = DummyPlayer(idx=2, species=[vuln, prot])

        self.assertEquals(defender.get_largest_attackable_species(carn), vuln)

    def test_get_hungry_vegetarians(self):

        player = DummyPlayer(1)

        hungry1 = Species(food=0, body=2, population=2)
        hungry2 = Species(food=0, body=2, population=1, traits=[Trait.CARNIVORE])
        not_hungry = Species(food=1, body=2, population=1, traits=[Trait.CARNIVORE], fat_food=0)

        player.species.append(not_hungry)
        player.species.append(hungry2)
        player.species.append(hungry1)

        self.assertListEqual(player.get_hungry_vegetarians(), [hungry1])

    def test_get_hungry_carnivores_and_can_attack(self):

        player = DummyPlayer()

        hungry1 = Species(food=0, body=1, population=1, traits=[Trait.CARNIVORE])
        hungry2 = Species(food=1, body=7, population=2, traits=[Trait.CARNIVORE, Trait.CLIMBING, Trait.AMBUSH])

        player.species.append(hungry2)
        player.species.append(hungry1)

        self.assertListEqual(player.get_hungry_carnivores(), [hungry2, hungry1])

        player2 = DummyPlayer(2)

        species1 = Species(food=1, body=2, population=1, traits=[Trait.BURROWING])
        species2 = Species(food=1, body=2, population=1, traits=[Trait.CLIMBING])
        species3 = Species(food=1, body=4, population=1, traits=[Trait.HARD_SHELL])
        species4 = Species(food=1, body=2, population=1, traits=[Trait.SYMBIOSIS])
        species5 = Species(food=1, body=2, population=2, traits=[Trait.HERDING])
        species6 = Species(food=1, body=2, population=2, traits=[Trait.SCAVENGER])
        species7 = Species(food=1, body=2, population=2, traits=[Trait.WARNING_CALL, Trait.CLIMBING])
        species8 = Species(food=1, body=2, population=2, traits=[Trait.LONG_NECK])
        player2.species.append(species8)
        player2.species.append(species7)
        player2.species.append(species6)
        player2.species.append(species5)
        player2.species.append(species4)
        player2.species.append(species3)
        player2.species.append(species2)
        player2.species.append(species1)

        players = [player2]

        possible_attackers = [hungry2]
        self.assertListEqual(player.get_hungry_carnivores_can_attack(players + [player]), possible_attackers)
