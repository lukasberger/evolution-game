from unittest import TestCase

from .data_definitions import DataDefinitions, unpack, irange
from .common.trait import Trait
from .common.trait_card import TraitCard


class UnpackTestCase(TestCase):

    def setUp(self):
        self.config = [
            ["test-key", "testkey", DataDefinitions.integer],
            ["test-key-opt", "testkeyopt", DataDefinitions.integer, DataDefinitions.OPTIONAL],
            ["test-key1", "testkey1", DataDefinitions.integer],
            ["test-key1-opt", "testkey1opt", DataDefinitions.integer, DataDefinitions.OPTIONAL],
            ["test-key2-opt", "testkey2opt", DataDefinitions.integer, DataDefinitions.OPTIONAL],
        ]


    def test_unpack_invalid_type(self):

        data = [
            ["test-key", "not-an-int"],
        ]

        with self.assertRaises(AssertionError):
            unpack(self.config, data)

    def test_unpack_valid_without_optionals(self):

        data = [
            ["test-key", 1],
            ["test-key1", 2]
        ]
        expected = {
            "testkey": 1,
            "testkey1": 2,
        }

        self.assertEqual(unpack(self.config, data), expected)

    def test_unpack_valid_without_optional_one(self):

        data = [
            ["test-key", 1],
            ["test-key1", 2],
            ["test-key2-opt", 3],
        ]
        expected = {
            "testkey": 1,
            "testkey1": 2,
            "testkey2opt": 3,
        }

        self.assertEqual(unpack(self.config, data), expected)

    def test_unpack_valid_without_optional_all(self):

        data = [
            ["test-key", 1],
            ["test-key-opt", 2],
            ["test-key1", 3],
            ["test-key1-opt", 4],
            ["test-key2-opt", 5],
        ]
        expected = {
            "testkey": 1,
            "testkeyopt": 2,
            "testkey1": 3,
            "testkey1opt": 4,
            "testkey2opt": 5,
        }

        self.assertEqual(unpack(self.config, data), expected)


class DataDefinitionsTestCase(TestCase):

    def test_types(self):

        food_value_range = TraitCard.FOOD_VALUE_RANGE
        food_value_carnivore_range = TraitCard.FOOD_VALUE_CARNIVORE_RANGE

        trait_card_true = [
            [food_value_range[0], Trait.LONG_NECK.value],
            [food_value_range[-1], Trait.FORAGING.value],
            [food_value_carnivore_range[0], Trait.CARNIVORE.value],
            [food_value_carnivore_range[-1], Trait.CARNIVORE.value],
        ]
        trait_card_false = [
            [food_value_range[0] - 1, Trait.LONG_NECK.value],
            [food_value_range[-1] + 1, Trait.FORAGING.value],
            [food_value_carnivore_range[0] - 1, Trait.CARNIVORE.value],
            [food_value_carnivore_range[-1] + 1, Trait.CARNIVORE.value],
            "hi",
            [0, "yo"],
        ]

        action4_true = [
            [0, [["population", 0, 0]], [["body", 0, 0]], [[0]], [[0, 0, 0]]],
            [0, [["population", 0, 0]], [], [], []],
            [0, [], [["body", 0, 0]], [], []],
            [0, [], [], [[0]], []],
            [0, [], [], [], [[0, 0, 0]]],
            [0, [], [], [], []],
        ]
        action4_false = [
            ["hi", [], [], [], []],
            [0, [["population!", 0, 0]], [], [], []],  # gp
            [0, [["population", -1, 0]], [], [], []],  # gp
            [0, [["population", 0, -1]], [], [], []],  # gp
            [0, [["population", -1, -1]], [], [], []],  # gp
            [0, [], [["body!", 0, 0]], [], []],  # gb
            [0, [], [["body", -1, 0]], [], []],  # gb
            [0, [], [["body", 0, -1]], [], []],  # gb
            [0, [], [["body", -1, -1]], [], []],  # gb
            [0, [], [], [[-1]], []],  # bt
            [0, [], [], [[1, -1]], []],  # bt
            [0, [], [], [[1, 0, -1]], []],  # bt
            [0, [], [], [[1, 0, 2, -1]], []],  # bt
            [0, [], [], [], [[0, 1, -1]]],  # rt
            [0, [], [], [], [[0, -1, 1]]],  # rt
            [0, [], [], [], [[-1, 0, 1]]],  # rt
            [0, [], [], [], [[-1, -1, 1]]],  # rt
            [0, [], [], [], [[-1, 0, -1]]],  # rt
            [0, [], [], [], [[1, -1, -1]]],  # rt
            [0, [], [], [], [[-1, -1, -1]]],  # rt
        ]

        cases = [
            (DataDefinitions.null, [None], [1, "string", False]),
            (DataDefinitions.array, [[], [1, 2]], [1, "string"]),
            (DataDefinitions.integer, [-10, 1, 10], ["string", 0.1, True, False]),
            (DataDefinitions.natural, [0, 12], [-1]),
            (DataDefinitions.natural_plus, [1, 12], [-1, 0]),
            (DataDefinitions.food_value, food_value_range, [-4, 3.3, 1.0]),
            (DataDefinitions.food_value_carnivore, food_value_carnivore_range, [-94, 3.3, 1.0]),
            (DataDefinitions.trait, [t for t in Trait], [-94, False, 1.0, "some random trait"]),
            (DataDefinitions.trait_card, trait_card_true, trait_card_false),
            (DataDefinitions.feeding_outcome, [False], [True]),
            (DataDefinitions.action4, action4_true, action4_false),
        ]

        for predicate, successes, failures in cases:
            for item in successes:
                self.assertTrue(predicate(item), msg="{} doesn't pass {}".format(item, predicate))
            for item in failures:
                self.assertFalse(predicate(item), msg="{} passes {}".format(item, predicate))

    def test_species(self):

        cases = [
            (False, []),
            (False, ["blah", "hey"]),
            (True, [["food", 0], ["body", 1], ["population", 1], ["traits", []], ["fat_food", 0]]),
            (True, [["food", 0], ["body", 1], ["population", 1], ["traits", []]]),
        ]

        for expected, data in cases:
            self.assertIs(expected, DataDefinitions.species(data))

    def test_player(self):

        s_valid1 = [["food", 0], ["body", 1], ["population", 1], ["traits", []], ["fat_food", 0]]
        s_valid2 = [["food", 0], ["body", 1], ["population", 1], ["traits", []]]

        cases = [
            (False, []),
            (False, ["blah", "hey"]),
            (False, [["id", 1], ["bag", 1], ["species", []], ["cards", []]]),
            (True, [["id", 1], ["species", []], ["bag", 1], ["cards", []]]),
            (True, [["id", 1], ["species", []], ["bag", 1]]),
            (False, [["id", 1], ["species", [123]], ["bag", 1]]),
            (True, [["id", 1], ["species", [s_valid1, s_valid2]], ["bag", 1]]),
        ]

        for expected, data in cases:
            self.assertIs(expected, DataDefinitions.player(data), data)

    def test_dealer(self):

        s_valid1 = [["food", 0], ["body", 1], ["population", 1], ["traits", []], ["fat_food", 0]]
        s_valid2 = [["food", 0], ["body", 1], ["population", 1], ["traits", []]]
        p_valid = [["id", 1], ["species", [s_valid1, s_valid2]], ["bag", 1]]

        cases = [
            (False, []),
            (False, ["blah", "hey"]),
            (True, [[p_valid], 12, []]),
        ]

        for expected, data in cases:
            self.assertIs(expected, DataDefinitions.dealer(data), data)


class IRangeTestCase(TestCase):

    def test_irange(self):
        self.assertEqual(irange(0, 1), range(0, 2))
