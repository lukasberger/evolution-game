"""
    Represents an Evolution trait card, containing a value and trait.
"""


from .trait import Trait


class TraitCard:
    """ Represents an Evolution trait card, containing a value and trait. """

    # inclusive
    FOOD_VALUE_MIN = -3
    FOOD_VALUE_MAX = 3
    FOOD_VALUE_RANGE = range(FOOD_VALUE_MIN, FOOD_VALUE_MAX + 1)

    FOOD_VALUE_CARNIVORE_MIN = -8
    FOOD_VALUE_CARNIVORE_MAX = 8
    FOOD_VALUE_CARNIVORE_RANGE = range(FOOD_VALUE_CARNIVORE_MIN, FOOD_VALUE_CARNIVORE_MAX + 1)

    DISPLAY_KEY_VALUE = "value"
    DISPLAY_KEY_TRAIT = "trait"

    def __init__(self, value, trait):
        """ Creates a new trait card.
        :param value: number value of the card
        :param trait: trait on the card
        """
        self.value = value
        self.trait = trait

    def __repr__(self):
        return "TraitCard(value={}, trait={})".format(self.value, repr(self.trait))

    def __str__(self):
        return self.__repr__()

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.value == other.value and self.trait == other.trait

    def __lt__(self, other):
        return self.trait < other.trait or (self.trait == other.trait and self.value < other.value)

    def __hash__(self):
        return hash((self.value, self.trait.value))

    def serialize(self):
        """ Creates a JSON-friendly representation of this object.
        :return: JSON-friendly representation of this object
        """
        return [
            self.value,
            self.trait.value,
        ]

    @classmethod
    def deserialize(cls, data):
        """ Converts a JSON representation of this object into a TraitCard
        :param data: JSON representation of this object
        :return: TraitCard
        """
        value, trait_data = data
        trait = Trait(trait_data)
        return cls(value, trait)

    def display(self):
        """ Returns a data representation of the trait card that can be used in a view
        :return: data representation of a trait card to be used in a view
        """
        return {
            self.DISPLAY_KEY_VALUE: self.value,
            self.DISPLAY_KEY_TRAIT: self.trait.value,
        }
