"""

    Codifies Evolution data definitions.

"""

from .common.trait import Trait
from .common.trait_card import TraitCard


class DataDefinitions:

    OPTIONAL = "optional"
    NAT_MAX = 7

    PLAYER_JSON_KEY_IDX = "id"
    PLAYER_JSON_KEY_BAG = "bag"
    PLAYER_JSON_KEY_SPECIES = "species"
    PLAYER_JSON_KEY_CARDS = "cards"

    SPECIES_JSON_KEY_FOOD = "food"
    SPECIES_JSON_KEY_BODY = "body"
    SPECIES_JSON_KEY_POPULATION = "population"
    SPECIES_JSON_KEY_TRAITS = "traits"
    SPECIES_JSON_KEY_FAT_FOOD = "fat-food"

    @staticmethod
    def null(value):
        return value is None

    @staticmethod
    def array(value):
        return isinstance(value, list)

    @staticmethod
    def integer(value):
        """ Represents an integer
        """
        return isinstance(value, int) and not isinstance(value, bool)

    @classmethod
    def natural(cls, value):
        """ Represents a Natural number
        """
        return cls.integer(value) and value >= 0

    @classmethod
    def natural_plus(cls, value):
        """ Represents a Natural+ number
        """
        return cls.natural(value) and value >= 1

    @classmethod
    def nat(cls, value):
        """ Represents a Nat
        """
        return cls.natural(value) and value <= cls.NAT_MAX

    @classmethod
    def food_value(cls, value):
        """ Represents FoodValue of a TraitCard
        """
        return cls.integer(value) and value in TraitCard.FOOD_VALUE_RANGE

    @classmethod
    def food_value_carnivore(cls, value):
        """ Represents FoodValue of a Carnivore TraitCard
        """
        return cls.integer(value) and value in TraitCard.FOOD_VALUE_CARNIVORE_RANGE

    @staticmethod
    def trait(value):
        """ Represents a Trait """
        try:
            Trait(value)
            return True
        except ValueError:
            return False

    @classmethod
    def trait_card(cls, value):
        """ Represents a TraitCard """
        if not cls.array(value):
            return False

        try:
            food_value, trait_data = value
            trait = Trait(trait_data)

            if trait == Trait.CARNIVORE:
                return cls.food_value_carnivore(food_value)
            else:
                return cls.food_value(food_value)

        except ValueError:
            return False

    @classmethod
    def dealer(cls, value):
        """ Represents a Dealer """
        try:
            assert DataDefinitions.array(value)
            assert len(value) == 3
            lop, watering_hole, loc = value
            assert DataDefinitions.array(lop) and all(cls.player(p) for p in lop)
            assert DataDefinitions.natural(watering_hole) and cls.natural(watering_hole)
            assert DataDefinitions.array(loc) and all(cls.trait_card(tc) for tc in loc)
        except AssertionError:
            return False
        return True

    @classmethod
    def player(cls, value):
        """ Represents a player """
        try:
            data_config = [
                [cls.PLAYER_JSON_KEY_IDX, "idx", cls.natural_plus],
                [cls.PLAYER_JSON_KEY_SPECIES, "species", cls.array],
                [cls.PLAYER_JSON_KEY_BAG, "bag", cls.natural],
                [cls.PLAYER_JSON_KEY_CARDS, "cards", cls.array, cls.OPTIONAL],
            ]

            parameters = unpack(data_config, value)
            assert all(cls.species(species) for species in parameters['species'])

            if "cards" in parameters:
                assert all(cls.trait_card(card) for card in parameters['cards'])

        except AssertionError:
            return False
        return True

    @classmethod
    def species(cls, value):
        """ Represents a species """
        try:
            data_config = [
                [cls.SPECIES_JSON_KEY_FOOD, "food", cls.natural],
                [cls.SPECIES_JSON_KEY_BODY, "body", cls.natural],
                [cls.SPECIES_JSON_KEY_POPULATION, "population", cls.natural],
                [cls.SPECIES_JSON_KEY_TRAITS, "traits", cls.array],
                [cls.SPECIES_JSON_KEY_FAT_FOOD, "fat_food", cls.natural, cls.OPTIONAL],
            ]

            parameters = unpack(data_config, value)
            assert all(cls.trait(trait) for trait in parameters['traits'])

        except AssertionError:
            return False
        return True

    @classmethod
    def feeding_outcome(cls, value):
        """ Represents a FeedingOutcome """
        # no feeding
        if value is False:
            return True
        # vegetarian
        if cls.natural(value):
            return True
        # fat tissue
        if cls.array(value) and len(value) == 2:
            species_index, tokens = value
            return cls.natural(species_index) and cls.nat(tokens)
        # carnivore
        if cls.array(value) and len(value) == 3:
            return all(cls.natural(index) for index in value)

        return False

    @classmethod
    def action4(cls, value):
        """ Represents an Action4 """
        if not (cls.array(value) and len(value) == 5):
            return False

        discard, gp, gb, bt, rt = value

        if not (cls.natural(discard) and
                cls.array(gp) and
                cls.array(gb) and
                cls.array(bt) and
                cls.array(rt)):
            return False

        if not all(all(cls.natural(c) for c in card_indices) for card_indices in bt):
            return False

        if not all((action == "population" and cls.natural(species_index) and cls.natural(card_index))
                   for action, species_index, card_index in gp):
            return False

        if not all((action == "body" and cls.natural(species_index) and cls.natural(card_index))
                   for action, species_index, card_index in gb):
            return False

        if not all((cls.natural(species_index) and cls.natural(card_index) and cls.natural(trait_slot))
                   for species_index, trait_slot, card_index in rt):
            return False

        return True

    @classmethod
    def deck(cls):
        """ Returns the list of all evolution cards """
        cards = []

        for trait in Trait:
            numbers = TraitCard.FOOD_VALUE_RANGE if trait != Trait.CARNIVORE else TraitCard.FOOD_VALUE_CARNIVORE_RANGE
            cards += [TraitCard(n, trait) for n in numbers]

        return cards



def irange(start, end):
    """ Inclusive range [start, end]
    :param start: start value
    :param end: end value
    :return: [start, end] range
    """
    return range(start, end + 1)


def unpack(config, data):
    """ Unpack the given Evolution-style JSON based on the given config.
      The Config is a list of ConfigItems, where a ConfigItem is one of:

        [JSONKey, ObjectAttribute, Predicate, OptionalFlag]

        or

        [JSONKey, ObjectAttribute, Predicate]

      and

        JSONKey is a String representing the key in the JSON
        ObjectAttribute is a String representing the attribute name of the object
        Predicate is a one of DataDefinition predicates
        OptionalFlag is DataDefinition.OPTIONAL


    Maps values at JSONKeys to the ObjectAttributes and returns
      dictionary representing the mapping.

    :param config: list of ConfigItems
    :param data: evolution-style JSON data representation of an object
    :return: dictionary of values
    """
    assert isinstance(data, list)
    values, data_key, data_len = {}, 0, len(data)
    required_config_items = len([item for item in config if item[-1] is not DataDefinitions.OPTIONAL])

    if data_len < required_config_items:
        raise AssertionError("{} items given, at least {} expected".format(data_len, required_config_items))

    for config_item in config:
        expected_key, key, predicate, *optional = config_item
        is_optional = (len(optional) == 1 and optional[0] is DataDefinitions.OPTIONAL)

        if is_optional and data_key == data_len:
            continue

        actual_key, value = data[data_key]

        if expected_key != actual_key:
            if is_optional:
                continue
            else:
                raise AssertionError("{} expected as the next key, {} given".format(expected_key, actual_key))

        assert predicate(value)
        values[key] = value

        data_key += 1

    return values
