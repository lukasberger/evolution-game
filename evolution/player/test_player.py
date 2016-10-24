from unittest import TestCase
from unittest.mock import MagicMock

from .player import Player

from ..common.trait import Trait
from ..common.trait_card import TraitCard
from ..common.species import Species
from ..common.feeding_outcome import FatTissueFeeding, VegetarianFeeding, CarnivoreFeeding, CannotFeed


class TestPlayerSerialize(TestCase):

    def test_serialize_deserialize(self):

        player = Player(1)
        expected = [['id', 1], ['species', []], ['bag', 0]]
        self.assertEqual(player.serialize(), expected)
        self.assertEqual(player.deserialize(player.serialize()).serialize(), expected)

        player = Player(1, cards=[TraitCard(1, Trait.CARNIVORE)])
        expected = [['id', 1], ['species', []], ['bag', 0], ['cards', [[1, Trait.CARNIVORE.value]]]]
        self.assertEqual(player.serialize(), expected)
        self.assertEqual(player.deserialize(player.serialize()).serialize(), expected)

    def test_repr(self):

        c1 = TraitCard(1, Trait.CARNIVORE)

        cases = [
            # id, species, bag, cards, expected id, expected species, expected bag, expected cards
            (1, None, None, None, 1, [], 0, None),
            (1, None, None, [c1], 1, [], 0, "[{}]".format(repr(c1))),
        ]

        for pid, species, bag, cards, pid_expected, species_expected, bag_expected, cards_expected in cases:
            player = Player(idx=pid, species=species, bag=bag, cards=cards)

            if cards_expected is not None:
                expected = "Player(idx={}, species={}, bag={}, cards={})".format(
                    pid_expected, species_expected, bag_expected, cards_expected)
            else:
                expected = "Player(idx={}, species={}, bag={})".format(
                    pid_expected, species_expected, bag_expected)

            self.assertEqual(repr(player), expected)

    def test_add_cards(self):

        player = Player(1)
        self.assertListEqual(player.cards, [])

        tc1 = TraitCard(0, Trait.CARNIVORE)
        tc2 = TraitCard(0, Trait.LONG_NECK)
        tc3 = TraitCard(0, Trait.FAT_TISSUE)

        player.add_cards([])
        self.assertListEqual(player.cards, [])

        player.add_cards([tc1])
        self.assertListEqual(player.cards, [tc1])

        player.add_cards([tc2, tc3])
        self.assertListEqual(player.cards, [tc1, tc2, tc3])

    def test_get_hungry_species(self):

        player = Player(1)

        hungry1 = Species(food=0, body=2, population=2)
        hungry2 = Species(food=0, body=2, population=1)
        not_hungry = Species(food=1, body=2, population=1, traits=[Trait.FAT_TISSUE], fat_food=0)

        player.species.append(not_hungry)
        player.species.append(hungry2)
        player.species.append(hungry1)

        self.assertListEqual(player.get_hungry_species(), [hungry2, hungry1])

    def test_feeding_choice(self):

        external = MagicMock()
        external.feed_next.return_value = False

        external_cannot_call = MagicMock()
        external_cannot_call.feed_next.side_effect = Exception("cannot be called")

        hungry1 = Species(food=1, body=1, population=1, traits=[Trait.CARNIVORE])
        hungry2 = Species(food=2, body=7, population=2, traits=[Trait.CARNIVORE, Trait.CLIMBING, Trait.AMBUSH])

        player = Player(1, species=[hungry2, hungry1], external=external_cannot_call)
        player2 = Player(1)

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

        # No hungry_species and no can_store_fat_tissue
        feeding_choice = player.feeding_choice(players, 4).content()
        self.assertIsInstance(feeding_choice, CannotFeed)

        hungry1 = Species(food=0, body=1, population=1, traits=[Trait.CLIMBING])
        hungry2 = Species(food=1, body=7, population=2, traits=[Trait.CARNIVORE])

        player = Player(1, species=[hungry2, hungry1])

        # auto feed vegetarian
        feeding_choice = player.feeding_choice(players, 4).content()
        self.assertIsInstance(feeding_choice, VegetarianFeeding)

        player = Player(1)

        hungry1 = Species(food=1, body=1, population=1, traits=[Trait.CLIMBING, Trait.FAT_TISSUE], fat_food=0)
        hungry2 = Species(food=1, body=7, population=2, traits=[Trait.CARNIVORE, Trait.CLIMBING, Trait.AMBUSH])

        player.species.append(hungry2)
        player.species.append(hungry1)

        # Not CannotFeed() nor VegetarianFeeding
        player.external = external
        external.feed_next.reset_mock()
        self.assertFalse(external.feed_next.called)
        player.feeding_choice(players, 4)
        self.assertTrue(external.feed_next.called)

    def test_get_neighbors(self):

        player = Player(1)

        species1 = Species(food=0, body=1, population=1, traits=[Trait.COOPERATION])
        species2 = Species(food=0, body=1, population=1, traits=[Trait.BURROWING])
        species3 = Species(food=0, body=1, population=1, traits=[Trait.FAT_TISSUE], fat_food=0)

        player.species.append(species1)
        player.species.append(species2)
        player.species.append(species3)

        self.assertIsNone(player.get_neighbors(0)[0])
        self.assertEquals(player.get_neighbors(0)[1], species2)

        self.assertEquals(player.get_neighbors(2)[0], species2)
        self.assertIsNone(player.get_neighbors(2)[1])

    def test_get_neighbors_same_species(self):
        player = Player(1)

        species1 = Species()
        species2 = Species()
        species3 = Species()

        player.species.append(species1)
        player.species.append(species2)
        player.species.append(species3)

        self.assertEquals(player.get_neighbors(1), (species1, species3))

    def test_feed_species(self):

        player = Player(1)

        species1 = Species(food=0, body=1, population=1, traits=[Trait.COOPERATION])
        species2 = Species(food=0, body=1, population=1, traits=[Trait.COOPERATION])
        species3 = Species(food=0, body=1, population=1, traits=[])
        species4 = Species(food=0, body=1, population=1, traits=[Trait.COOPERATION])

        player.species.append(species1)
        player.species.append(species2)
        player.species.append(species3)
        player.species.append(species4)

        self.assertEquals(player.feed_species(0, 4), 3)
        self.assertEquals(player.species[0].food, 1)
        self.assertEquals(player.species[1].food, 1)

    def test_cooperate(self):

        player = Player(1)

        species1 = Species(food=0, body=1, population=1, traits=[Trait.COOPERATION])
        species2 = Species(food=0, body=1, population=1, traits=[Trait.COOPERATION])
        species3 = Species(food=0, body=1, population=1, traits=[])
        species4 = Species(food=0, body=1, population=1, traits=[Trait.COOPERATION])

        player.species.append(species1)
        player.species.append(species2)
        player.species.append(species3)
        player.species.append(species4)

        self.assertEquals(player.cooperate(0, 4), 2)

    def test_store_fat_tissue(self):

        player = Player(1)

        species1 = Species(food=1, body=1, population=1, traits=[Trait.FAT_TISSUE], fat_food=0)
        player.species.append(species1)

        player.store_fat_tissue(0, 1)
        self.assertEquals(player.species[0].fat_food, 1)

    def test_hurt_species(self):

        player = Player(1)

        species1 = Species(food=1, body=1, population=1, traits=[Trait.LONG_NECK])
        species2 = Species(food=1, body=2, population=2, traits=[Trait.HORNS])

        player.species.append(species2)
        player.species.append(species1)

        self.assertTupleEqual(player.hurt_species(0, 1), (False, True))
        self.assertTupleEqual(player.hurt_species(1, 1), (True, False))

        self.assertEquals(player.species[0].traits[0], Trait.HORNS)

    def test_scavenge(self):

        player = Player(1)

        species1 = Species(food=1, body=2, population=2, traits=[Trait.SCAVENGER])
        species2 = Species(food=1, body=2, population=1, traits=[Trait.SCAVENGER])

        player.species.append(species2)
        player.species.append(species1)

        self.assertEquals(player.scavenge(2), 1)
        self.assertEquals(species1.food, 2)

        self.assertEquals(player.scavenge(1), 0)

        species3 = Species(food=1, body=2, population=5, traits=[Trait.SCAVENGER])
        player.species.append(species3)

        self.assertEquals(player.scavenge(1), 1)
        self.assertEquals(species3.food, 2)

    def test_auto_traits_no_auto_traits(self):
        # no auto feeding traits
        s1 = Species(food=1, body=1, population=1)
        s1_before = s1.serialize()

        s1_owner = MagicMock()
        idx = 0
        wh = 10

        s1.auto_traits(s1_owner, idx, wh)

        s1_after = s1.serialize()
        self.assertEqual(s1_before, s1_after)
        self.assertFalse(s1_owner.feed_species.called)

    def test_auto_traits_all_traits(self):
        # all auto_feeding traits
        s1 = Species(food=0, body=2, population=1, fat_food=2,
                     traits=[Trait.FERTILE, Trait.LONG_NECK, Trait.FAT_TISSUE])
        s1_owner = Player(1, species=[s1])

        s1_expected = Species.deserialize(s1.serialize())
        s1_expected.population += 1
        s1_expected.food += (1 + 1)  # 1 from long_neck, 1 from fat tissue
        s1_expected.fat_food -= 1  # 1 from long_neck, 1 from fat tissue

        idx = 0
        wh = 10

        tokens_consumed = s1.auto_traits(s1_owner, idx, wh)
        self.assertEqual(tokens_consumed, 1)

        s1_after = s1.serialize()
        self.assertEqual(s1_expected.serialize(), s1_after)

    def test_auto_traits_long_neck_cooperation(self):
        # no auto feeding traits
        s1 = Species(food=0, body=2, population=4, traits=[Trait.FORAGING, Trait.LONG_NECK, Trait.COOPERATION])
        s2 = Species(food=0, body=2, population=4)
        s1_owner = Player(1, species=[s1, s2])

        s1_expected = Species.deserialize(s1.serialize())
        s1_expected.food += 2  # 1 from long_neck, 1 from foraging

        s2_expected = Species.deserialize(s2.serialize())
        s2_expected.food += 2  # cooperation triggered twice

        idx = 0
        wh = 10

        tokens_consumed = s1.auto_traits(s1_owner, idx, wh)
        self.assertEqual(tokens_consumed, 4)

        s1_after = s1.serialize()
        s2_after = s2.serialize()
        self.assertEqual(s1_expected.serialize(), s1_after)
        self.assertEqual(s2_expected.serialize(), s2_after)

    def test_display(self):

        s1 = Species(food=0, body=2, population=4, traits=[Trait.FORAGING, Trait.LONG_NECK, Trait.COOPERATION])
        s2 = Species(food=0, body=2, population=4)
        s1_owner = Player(1, bag=4, species=[s1, s2], cards=[TraitCard(-2, Trait.CARNIVORE)])

        s1_owner_expected = {
            Player.DATA_KEY_IDX: 1,
            Player.DATA_KEY_BAG: 4,
            Player.DATA_KEY_SPECIES: [s.display() for s in s1_owner.species],
            Player.DATA_KEY_CARDS: [tc.display() for tc in s1_owner.cards],
        }

        self.assertEqual(s1_owner.display(), s1_owner_expected)


class FeedingChoiceTestCase(TestCase):

    def test_feeding_choice_1_fat_tissue(self):

        external_cannot_call = MagicMock()
        external_cannot_call.feed_next.side_effect = Exception("cannot be called")

        # only 1 choice, fat tissue
        p = Player(1, species=[
            # hungry carnivore with no valid targets
            Species(food=0, body=2, population=1, traits=[Trait.CARNIVORE]),
            # species that can store more fat tokens
            Species(food=1, body=2, population=1, traits=[Trait.FAT_TISSUE, Trait.CLIMBING], fat_food=0)
        ])

        e1 = Player(2, species=[
            Species(traits=[Trait.CLIMBING]),
        ])
        e2 = Player(3, species=[
            Species(traits=[]),
            Species(traits=[Trait.WARNING_CALL, Trait.CLIMBING]),
            Species(traits=[]),
        ])

        p.external = external_cannot_call
        feeding = p.feeding_choice([e1, e2], 2).content()
        self.assertIsInstance(feeding, FatTissueFeeding)
        self.assertEqual(feeding.species_index, 1)
        self.assertEqual(feeding.food_tokens, 2)

        feeding = p.feeding_choice([e1, e2], 1).content()
        self.assertIsInstance(feeding, FatTissueFeeding)
        self.assertEqual(feeding.species_index, 1)
        self.assertEqual(feeding.food_tokens, 1)

    def test_feeding_choice_1_vegetarian(self):

        external_cannot_call = MagicMock()
        external_cannot_call.feed_next.side_effect = Exception("cannot be called")

        # only 1 choice, fat tissue
        p = Player(1, species=[
            # hungry carnivore with no valid targets
            Species(food=0, body=2, population=1, traits=[Trait.CARNIVORE]),
            # species that cannot store any more fat tokens
            Species(food=1, body=2, population=1, traits=[Trait.FAT_TISSUE, Trait.CLIMBING], fat_food=2),
            # hungry vegetarian
            Species(food=0, body=2, population=1, traits=[Trait.CLIMBING])
        ])
        p.external = external_cannot_call

        e1 = Player(2, species=[
            Species(traits=[Trait.CLIMBING]),
        ])
        e2 = Player(3, species=[
            Species(traits=[]),
            Species(traits=[Trait.WARNING_CALL, Trait.CLIMBING]),
            Species(traits=[]),
        ])

        feeding = p.feeding_choice([e1, e2], 2).content()
        self.assertIsInstance(feeding, VegetarianFeeding)
        self.assertEqual(feeding.species_index, 2)

    def test_feeding_choice_1_carnivore_1_target_other_players(self):

        external_cannot_call = MagicMock()
        external_cannot_call.feed_next.side_effect = Exception("cannot be called")

        # only 1 choice, fat tissue
        p = Player(1, species=[
            # hungry carnivore with no valid targets
            Species(food=0, body=2, population=1, traits=[Trait.CARNIVORE]),
            # species that cannot store any more fat tokens
            Species(food=1, body=2, population=1, traits=[Trait.FAT_TISSUE, Trait.CLIMBING], fat_food=2),
            # full vegetarian
            Species(food=1, body=2, population=1, traits=[Trait.CLIMBING])
        ])
        p.external = external_cannot_call

        e1 = Player(2, species=[
            Species(traits=[Trait.CLIMBING]),
        ])
        e2 = Player(3, species=[
            Species(traits=[]),
            Species(traits=[Trait.WARNING_CALL]),
            Species(traits=[]),
        ])

        feeding = p.feeding_choice([e1, e2], 2).content()
        self.assertIsInstance(feeding, CarnivoreFeeding)
        self.assertEqual(feeding.species_index, 0)
        self.assertEqual(feeding.player_index, 1)
        self.assertEqual(feeding.defender_index, 1)

    def test_feeding_choice_1_carnivore_1_target_self(self):

        external = MagicMock()
        external.feed_next.return_value = False

        # only 1 choice, fat tissue
        p = Player(1, species=[
            # hungry carnivore with no valid targets
            Species(food=0, body=2, population=1, traits=[Trait.CARNIVORE]),
            # species that cannot store any more fat tokens
            Species(food=1, body=2, population=1, traits=[Trait.FAT_TISSUE, Trait.CLIMBING], fat_food=2),
            # full vegetarian
            Species(food=1, body=2, population=1, traits=[])
        ])
        p.external = external

        e1 = Player(2, species=[
            Species(traits=[Trait.CLIMBING]),
        ])
        e2 = Player(3, species=[
            Species(traits=[]),
            Species(traits=[Trait.WARNING_CALL, Trait.CLIMBING]),
            Species(traits=[]),
        ])

        self.assertFalse(external.feed_next.called)
        p.feeding_choice([e1, e2], 2)
        self.assertTrue(external.feed_next.called)

    def test_feeding_choice_1_carnivore_1_other_1_target_self(self):

        external = MagicMock()
        external.feed_next.return_value = False

        # only 1 choice, fat tissue
        p = Player(1, species=[
            # hungry carnivore with no valid targets
            Species(food=0, body=2, population=1, traits=[Trait.CARNIVORE]),
            # species that cannot store any more fat tokens
            Species(food=1, body=2, population=1, traits=[Trait.FAT_TISSUE, Trait.CLIMBING], fat_food=2),
            # full vegetarian
            Species(food=1, body=2, population=1, traits=[])
        ])
        p.external = external

        e1 = Player(2, species=[
            Species(traits=[Trait.CLIMBING]),
        ])
        e2 = Player(3, species=[
            Species(traits=[]),
            Species(traits=[Trait.WARNING_CALL]),
            Species(traits=[]),
        ])

        self.assertFalse(external.feed_next.called)
        p.feeding_choice([e1, e2], 2)
        self.assertTrue(external.feed_next.called)
