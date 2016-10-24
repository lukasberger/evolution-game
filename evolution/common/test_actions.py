from unittest import TestCase

from .actions import Actions, GrowPopulation, GrowBody, BoardTransfer, ReplaceTrait

from .species import Species
from .trait import Trait
from .trait_card import TraitCard

from ..player.player import Player


class ActionsTestCase(TestCase):

    def test_validate(self):

        tc_1_car = TraitCard(1, Trait.CARNIVORE)
        tc_2_lon = TraitCard(2, Trait.LONG_NECK)
        tc_3_cli = TraitCard(3, Trait.CLIMBING)
        tc_7_car = TraitCard(7, Trait.CARNIVORE)
        tc_8_car = TraitCard(8, Trait.CARNIVORE)

        many_cards = [TraitCard(i, Trait.CARNIVORE) for i in range(-8, 8)]
        # card at 0 is discarded
        many_gp = [GrowPopulation(0, i + 1) for i in range(Species.MAXIMUM_POPULATION)]
        many_gb = [GrowBody(0, i + 1) for i in range(Species.MAXIMUM_BODY + 1)]

        cases = [
            ("card used multiple times",
             (Actions(0, grow_population=[GrowPopulation(0, 0)]), [Species()], [tc_1_car], False)),
            ("card out of range",
             (Actions(0, grow_population=[GrowPopulation(0, 1)], board_transfer=[BoardTransfer(2, [3, 4, 5])]),
              [Species()], [], False)),
            ("change existing species",
             (Actions(0, grow_population=[GrowPopulation(0, 1)]), [Species()], [tc_1_car, tc_2_lon], True)),
            ("add new species and perform grow/replace",
             (Actions(0, grow_population=[GrowPopulation(0, 1)], board_transfer=[BoardTransfer(2, [])]),
              [], [tc_1_car, tc_2_lon, tc_3_cli], True)),
            ("use too many cards to raise population of one species",
             (Actions(0, grow_population=many_gp), [Species()], many_cards, False)),
            ("use too many cards to raise body of one species",
             (Actions(0, grow_body=many_gb), [Species()], many_cards, False)),
            ("replace the same trait twice",
             (Actions(0, replace_trait=[ReplaceTrait(0, 0, 3), ReplaceTrait(0, 0, 2)]),
              [Species(traits=[Trait.CARNIVORE, Trait.LONG_NECK])],
              [tc_1_car, tc_2_lon, tc_3_cli, tc_8_car],
              True)),
            ("replace trait with another and then the same one with a duplicate of existing",
             (Actions(0, replace_trait=[ReplaceTrait(0, 0, 3), ReplaceTrait(0, 0, 1)]),
              [Species(traits=[Trait.CARNIVORE, Trait.LONG_NECK])],
              [tc_1_car, tc_2_lon, tc_3_cli, tc_8_car],
              False)),
            ("replace trait on a new species",
             (Actions(0, board_transfer=[BoardTransfer(1, [2])], replace_trait=[ReplaceTrait(0, 0, 3)]),
              [],
              [tc_1_car, tc_2_lon, tc_3_cli, tc_8_car],
              True)),
            ("replace trait on a new species with the same trait",
             (Actions(0, board_transfer=[BoardTransfer(1, [2, 3])], replace_trait=[ReplaceTrait(0, 1, 4)]),
              [],
              [tc_1_car, tc_2_lon, tc_3_cli, tc_7_car, tc_7_car],
              True)),
            ("replace trait on a new species that doesn't have the trait slot occupied",
             (Actions(0, board_transfer=[BoardTransfer(1, [2])], replace_trait=[ReplaceTrait(0, 2, 3)]),
              [],
              [tc_1_car, tc_2_lon, tc_3_cli, tc_8_car],
              False)),
            ("replace trait on a new species to be a duplicate of an existing trait",
             (Actions(0, board_transfer=[BoardTransfer(1, [2, 3])], replace_trait=[ReplaceTrait(0, 0, 4)]),
              [],
              [tc_1_car, tc_2_lon, tc_3_cli, tc_7_car, tc_7_car],
              False)),
        ]

        for msg, (actions, species, cards, expected) in cases:
            player = Player(0, species=species, cards=cards)
            self.assertIs(actions.validate(player), expected, msg)

    def test_serialize_deserialize(self):
        data = [
            0,
            [["population", 1, 2]],
            [["body", 3, 4]],
            [[1], [2, 3], [4, 5, 6], [7, 8, 9, 0]],
            [[0, 1, 2], [3, 4, 5]],
        ]

        action = Actions(
            discard=0,
            grow_population=[GrowPopulation(1, 2)],
            grow_body=[GrowBody(3, 4)],
            board_transfer=[BoardTransfer(1, []), BoardTransfer(2, [3]),
                            BoardTransfer(4, [5, 6]), BoardTransfer(7, [8, 9, 0])],
            replace_trait=[ReplaceTrait(0, 1, 2), ReplaceTrait(3, 4, 5)]
        )

        self.assertEqual(action.serialize(), data)
        self.assertEqual(Actions.deserialize(data).serialize(), data)

    def test_used_cards(self):
        action = Actions(
            discard=0,
            grow_population=[GrowPopulation(1, 2)],
            grow_body=[GrowBody(3, 4)],
            board_transfer=[BoardTransfer(1, []), BoardTransfer(2, [3]),
                            BoardTransfer(4, [5, 6]), BoardTransfer(7, [8, 9, 0])],
            replace_trait=[ReplaceTrait(0, 1, 2), ReplaceTrait(3, 4, 5)]
        )

        self.assertEqual(action.used_cards(), [0,
                                               2,
                                               4,
                                               1, 2, 3, 4, 5, 6, 7, 8, 9, 0,
                                               2, 5])

class ApplyActionsTestCase(TestCase):

    def species(self, *args, **kwargs):
        original = Species(*args, **kwargs)
        expected = Species(*args, **kwargs)
        return original, expected

    def test_no_actions(self):
        """ No actions given in the actions object, except for discard """
        tc0 = TraitCard(4, Trait.CARNIVORE)
        player = Player(1, species=[], bag=0, cards=[tc0])

        actions = Actions(discard=0)
        self.assertEqual(player.cards, [tc0])
        actions.apply(player)
        self.assertEqual(player.cards, [])

    def test_board_transfer(self):
        """ Tests board transfer """
        tc0 = TraitCard(4, Trait.CARNIVORE)

        # s0 gets not species
        tc1 = TraitCard(0, Trait.WARNING_CALL)
        s0 = Species(traits=[])
        # s1 gets warning call
        tc2 = TraitCard(0, Trait.WARNING_CALL)
        tc3 = TraitCard(0, Trait.WARNING_CALL)
        s1 = Species(traits=[tc3.trait])
        # s2 gets warning call, long neck
        tc4 = TraitCard(0, Trait.WARNING_CALL)
        tc5 = TraitCard(0, Trait.WARNING_CALL)
        tc6 = TraitCard(0, Trait.LONG_NECK)
        s2 = Species(traits=[tc5.trait, tc6.trait])
        # s3 gets warning call, long neck, symbiosis
        tc7 = TraitCard(0, Trait.WARNING_CALL)
        tc8 = TraitCard(0, Trait.WARNING_CALL)
        tc9 = TraitCard(0, Trait.LONG_NECK)
        tc10 = TraitCard(0, Trait.SYMBIOSIS)
        s3 = Species(traits=[tc8.trait, tc9.trait, tc10.trait])

        player_cards = [tc0, tc1, tc2, tc3, tc4, tc5, tc6, tc7, tc8, tc9, tc10]
        player = Player(1, species=[], bag=0, cards=player_cards)

        board_transfers = [
            BoardTransfer(1, []),  # no traits,
            BoardTransfer(2, [3]),  # 1 trait
            BoardTransfer(4, [5, 6]),  # 2 traits`
            BoardTransfer(7, [8, 9, 10]),  # 3 traits
        ]

        actions = Actions(discard=0, board_transfer=board_transfers)
        self.assertEqual(len(player_cards), 11)
        self.assertEqual(len(player.species), 0)
        self.assertEqual(player.cards, player_cards)

        actions.apply(player)

        self.assertEqual(player.cards, [])
        self.assertEqual(len(player.species), len(board_transfers))
        self.assertEqual(player.species, [s0, s1, s2, s3])

    def test_grow_population(self):

        tc0 = TraitCard(4, Trait.CARNIVORE)
        tc1 = TraitCard(1, Trait.LONG_NECK)
        tc2 = TraitCard(2, Trait.HARD_SHELL)
        tc3 = TraitCard(-2, Trait.HARD_SHELL)

        s0, s0_expected = self.species()
        s1, s1_expected = self.species()
        s2, s2_expected = self.species()

        cards = [tc0, tc1, tc2, tc3]
        player = Player(1, species=[s0, s1, s2], bag=0, cards=cards)

        grow_population = [
            GrowPopulation(0, 2),
            GrowPopulation(0, 1),
            GrowPopulation(2, 3),
        ]

        s0_expected.population += 2
        s2_expected.population += 1

        actions = Actions(discard=0, grow_population=grow_population)
        self.assertEqual(player.species, [s0, s1, s2])
        self.assertEqual(player.cards, cards)

        self.assertNotEqual(s0, s0_expected)
        self.assertNotEqual(s2, s2_expected)
        self.assertEqual(s1, s1_expected)

        actions.apply(player)

        self.assertEqual(player.species, [s0, s1, s2])
        self.assertEqual(player.cards, [])

        self.assertEqual(s0, s0_expected)
        self.assertEqual(s1, s1_expected)
        self.assertEqual(s2, s2_expected)

    def test_grow_body(self):

        tc0 = TraitCard(4, Trait.CARNIVORE)
        tc1 = TraitCard(1, Trait.LONG_NECK)
        tc2 = TraitCard(2, Trait.HARD_SHELL)
        tc3 = TraitCard(-2, Trait.HARD_SHELL)

        s0, s0_expected = self.species()
        s1, s1_expected = self.species()
        s2, s2_expected = self.species()

        cards = [tc0, tc1, tc2, tc3]
        player = Player(1, species=[s0, s1, s2], bag=0, cards=cards)

        grow_body = [
            GrowBody(0, 2),
            GrowBody(0, 1),
            GrowBody(2, 3),
        ]

        s0_expected.body += 2
        s2_expected.body += 1

        actions = Actions(discard=0, grow_body=grow_body)
        self.assertEqual(player.species, [s0, s1, s2])
        self.assertEqual(player.cards, cards)

        self.assertNotEqual(s0, s0_expected)
        self.assertNotEqual(s2, s2_expected)
        self.assertEqual(s1, s1_expected)

        actions.apply(player)

        self.assertEqual(player.species, [s0, s1, s2])
        self.assertEqual(player.cards, [])

        self.assertEqual(s0, s0_expected)
        self.assertEqual(s1, s1_expected)
        self.assertEqual(s2, s2_expected)

    def test_replace_trait(self):

        tc0 = TraitCard(4, Trait.CARNIVORE)
        tc1 = TraitCard(1, Trait.LONG_NECK)
        tc2 = TraitCard(2, Trait.HARD_SHELL)
        tc3 = TraitCard(-2, Trait.HARD_SHELL)

        s0, s0_expected = self.species()
        s1, s1_expected = self.species(traits=[Trait.CARNIVORE, Trait.HARD_SHELL])
        s2, s2_expected = self.species(traits=[Trait.SCAVENGER, Trait.SYMBIOSIS])

        cards = [tc0, tc1, tc2, tc3]
        player = Player(1, species=[s0, s1, s2], bag=0, cards=cards)

        replace_trait = [
            ReplaceTrait(1, 1, 1),
            ReplaceTrait(2, 0, 3)
        ]

        s1_expected.traits = [Trait.CARNIVORE, cards[1].trait]
        s2_expected.traits = [cards[3].trait, Trait.SYMBIOSIS]

        actions = Actions(discard=0, replace_trait=replace_trait)
        self.assertEqual(player.species, [s0, s1, s2])
        self.assertEqual(player.cards, cards)

        self.assertEqual(s0, s0_expected)
        self.assertNotEqual(s1, s1_expected)
        self.assertNotEqual(s2, s2_expected)

        actions.apply(player)

        self.assertEqual(player.species, [s0, s1, s2])
        self.assertEqual(player.cards, [tc2])

        self.assertEqual(s0, s0_expected)
        self.assertEqual(s1, s1_expected)
        self.assertEqual(s2, s2_expected)




class GrowActionTestCase(TestCase):

    def test_serialize_deserialize(self):
        action = GrowPopulation(0, 1)
        serialized = action.serialize()
        self.assertEqual(serialized, ["population", 0, 1])
        deserialized = GrowPopulation.deserialize(serialized)
        self.assertEqual(deserialized.serialize(), ["population", 0, 1])

        action = GrowBody(0, 1)
        serialized = action.serialize()
        self.assertEqual(serialized, ["body", 0, 1])
        deserialized = GrowBody.deserialize(serialized)
        self.assertEqual(deserialized.serialize(), ["body", 0, 1])

    def test_validate_population(self):

        # ( species_index, card_index, species, cards, valid? )
        cases = [
            ("player has 1 species and 1 card, valid",
             (0, 0, [Species()], [TraitCard(1, Trait.CARNIVORE)], True)),
            ("player has 0 species, but 1 is added with gp, and 1 card, valid",
             (0, 0, [], [TraitCard(1, Trait.CARNIVORE)], True)),
            ("species cannot grow population",
             (0, 0, [Species(population=Species.MAXIMUM_POPULATION)], [TraitCard(1, Trait.CARNIVORE)], False))

        ]

        for msg, (species_index, card_index, species, cards, valid) in cases:
            action = GrowPopulation(species_index, card_index)
            player = Player(0, species=species, cards=cards)
            actions = Actions(0, grow_population=[action], board_transfer=[BoardTransfer(0, 1)])
            self.assertIs(GrowPopulation.validate(player, actions), valid, msg)

    def test_validate_body(self):

        # ( species_index, card_index, species, cards, valid? )
        cases = [
            ("player has 1 species and 1 card, valid",
             (0, 0, [Species()], [TraitCard(1, Trait.CARNIVORE)], True)),
            ("player has 0 species, but 1 is added with gp, and 1 card, valid",
             (0, 0, [], [TraitCard(1, Trait.CARNIVORE)], True)),
            ("species cannot grow population",
             (0, 0, [Species(body=Species.MAXIMUM_BODY)], [TraitCard(1, Trait.CARNIVORE)], False))

        ]

        for msg, (species_index, card_index, species, cards, valid) in cases:
            action = GrowBody(species_index, card_index)
            player = Player(0, species=species, cards=cards)
            actions = Actions(0, grow_body=[action], board_transfer=[BoardTransfer(0, 1)])
            self.assertIs(GrowBody.validate(player, actions), valid, msg)

    def test_apply_population(self):

        player = Player(0, species=[Species(population=2)], cards=[TraitCard(1, Trait.CARNIVORE)])
        player_expected = Player(0, species=[Species(population=3)], cards=[TraitCard(1, Trait.CARNIVORE)])
        action = GrowPopulation(0, 0)

        self.assertNotEqual(player.serialize(), player_expected.serialize())
        action.apply(player)
        self.assertEqual(player.serialize(), player_expected.serialize())

    def test_apply_body(self):

        player = Player(0, species=[Species(body=2)], cards=[TraitCard(1, Trait.CARNIVORE)])
        player_expected = Player(0, species=[Species(body=3)], cards=[TraitCard(1, Trait.CARNIVORE)])
        action = GrowBody(0, 0)

        self.assertNotEqual(player.serialize(), player_expected.serialize())
        action.apply(player)
        self.assertEqual(player.serialize(), player_expected.serialize())


class BoardTransferTestCase(TestCase):

    def test_serialize_deserialize(self):

        cases = [
            # card_index, trait_card_indices, expected
            (0, [], [0]),
            (1, [2], [1, 2]),
            (1, [2, 3], [1, 2, 3]),
            (3, [1, 2, 5], [3, 1, 2, 5]),
        ]

        for card_index, trait_card_indices, expected in cases:
            action = BoardTransfer(card_index, trait_card_indices)
            serialized = action.serialize()
            self.assertEqual(serialized, expected)
            deserialized = BoardTransfer.deserialize(serialized)
            self.assertEqual(deserialized.serialize(), expected)

    def test_validate(self):

        tc_1_car = TraitCard(1, Trait.CARNIVORE)
        tc_2_lon = TraitCard(2, Trait.LONG_NECK)
        tc_3_cli = TraitCard(3, Trait.CLIMBING)
        tc_8_car = TraitCard(8, Trait.CARNIVORE)

        cases = [
            ([tc_1_car], [0], True),
            ([tc_1_car, tc_2_lon], [1, 0], True),
            ([tc_1_car, tc_2_lon, tc_3_cli], [0, 2, 1], True),
            ([tc_1_car, tc_2_lon, tc_3_cli, tc_8_car], [1, 0, 2, 3], False),
        ]

        for cards, bt, valid in cases:
            player = Player(0, species=[], cards=cards)
            action = BoardTransfer.deserialize(bt)
            actions = Actions(0, board_transfer=[action])
            self.assertIs(BoardTransfer.validate(player, actions), valid)

    def test_apply(self):

        tc_1_car = TraitCard(1, Trait.CARNIVORE)
        tc_2_lon = TraitCard(2, Trait.LONG_NECK)
        tc_3_cli = TraitCard(3, Trait.CLIMBING)
        tc_8_car = TraitCard(8, Trait.CARNIVORE)

        cases = [
            ([tc_1_car], Species(), [0]),
            ([tc_1_car, tc_2_lon], Species(traits=[Trait.CARNIVORE]), [1, 0]),
            ([tc_1_car, tc_2_lon, tc_3_cli], Species(traits=[Trait.CLIMBING, Trait.LONG_NECK]), [0, 2, 1]),
            ([tc_1_car, tc_2_lon, tc_3_cli, tc_8_car],
             Species(traits=[Trait.LONG_NECK, Trait.CLIMBING, Trait.CARNIVORE]), [0, 1, 2, 3]),
        ]

        for cards, species, bt in cases:
            player = Player(0, species=[], cards=cards)
            player_expected = Player(0, species=[species], cards=cards)
            action = BoardTransfer.deserialize(bt)

            self.assertNotEqual(player.serialize(), player_expected.serialize())
            action.apply(player)
            self.assertEqual(player.serialize(), player_expected.serialize())


class ReplaceTraitTestCase(TestCase):

    def test_serialize_deserialize(self):

        action = ReplaceTrait(0, 1, 2)
        expected = [0, 1, 2]
        serialized = action.serialize()
        self.assertEqual(serialized, expected)
        deserialized = ReplaceTrait.deserialize(serialized)
        self.assertEqual(deserialized.serialize(), expected)

    def test_validate(self):

        tc_1_car = TraitCard(1, Trait.CARNIVORE)
        tc_2_lon = TraitCard(2, Trait.LONG_NECK)
        tc_3_cli = TraitCard(3, Trait.CLIMBING)
        tc_8_car = TraitCard(8, Trait.CARNIVORE)

        cards = [tc_1_car, tc_2_lon, tc_3_cli, tc_8_car]

        cases = [
            # no species
            ([], [0, 1, 2], False),
            # no traits
            ([Species(traits=[])], [0, 1, 2], False),
            # successful replace
            ([Species(traits=[Trait.CARNIVORE])], [0, 0, 1], True),
            # no slot
            ([Species(traits=[Trait.CARNIVORE])], [0, 1, 1], False),
            # replace trait with same trait
            ([Species(traits=[Trait.CARNIVORE])], [0, 0, 0], True),
            # trait already exist
            ([Species(traits=[Trait.CARNIVORE, Trait.LONG_NECK])], [0, 1, 0], False),
        ]

        for species, rt, valid in cases:
            player = Player(0, species=species, cards=cards)
            action = ReplaceTrait.deserialize(rt)
            actions = Actions(0, replace_trait=[action])
            self.assertIs(ReplaceTrait.validate(player, actions), valid)

    def test_apply(self):

        tc_1_car = TraitCard(1, Trait.CARNIVORE)
        tc_2_lon = TraitCard(2, Trait.LONG_NECK)
        tc_3_cli = TraitCard(3, Trait.CLIMBING)
        tc_8_car = TraitCard(8, Trait.CARNIVORE)

        cards = [tc_1_car, tc_2_lon, tc_3_cli, tc_8_car]

        cases = [
            # successful replace
            ([Species(traits=[Trait.CARNIVORE])], [Species(traits=[Trait.LONG_NECK])], [0, 0, 1]),
            # replace trait with same trait
            ([Species(traits=[Trait.CARNIVORE])], [Species(traits=[Trait.CARNIVORE])], [0, 0, 0]),
        ]

        for species, species_expected, rt in cases:
            player = Player(0, species=species, cards=cards)
            player_expected = Player(0, species=species, cards=cards)
            action = ReplaceTrait.deserialize(rt)

            action.apply(player)
            self.assertEqual(player.serialize(), player_expected.serialize())
