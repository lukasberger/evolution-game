"""
    Implements the Evolution Species Board

    JSONSpecies is one of:

        [["food",Nat],
         ["body",Nat],
         ["population",Nat],
         ["traits",LOT]]

        [["food",Nat],
         ["body",Nat],
         ["population",Nat],
         ["traits",LOT]
         ["fat-food" ,Nat]]
        if the species has the "fat-tissue" trait and fat-food > 0

"""

from ..data_definitions import DataDefinitions
from .trait import Trait, HARD_SHELL_THRESHOLD


class Species:
    """ Represents a species board
    """

    MINIMUM_BODY = 0
    MAXIMUM_BODY = 7

    MINIMUM_POPULATION = 0
    MAXIMUM_POPULATION = 7

    MINIMUM_FOOD = 0

    MINIMUM_TRAITS = 0
    MAXIMUM_TRAITS = 3

    MINIMUM_FAT_FOOD = 0

    DEFAULT_FOOD = MINIMUM_FOOD
    DEFAULT_POPULATION = MINIMUM_POPULATION + 1
    DEFAULT_BODY = MINIMUM_BODY
    DEFAULT_FAT_FOOD = MINIMUM_FAT_FOOD

    BITE_SIZE = 1

    POPULATION_GROWTH = 1
    BODY_GROWTH = 1

    # Display method constants
    DISPLAY_KEY_FOOD = "food"
    DISPLAY_KEY_BODY = "body"
    DISPLAY_KEY_POPULATION = "population"
    DISPLAY_KEY_TRAITS = "traits"
    DISPLAY_KEY_FAT_FOOD = "fat-food"

    def __init__(self, food=None, body=None, population=None, traits=None, fat_food=None):
        """ Creates a new Species board with the given data
        :param food: number of food tokens fed to this species
        :param body: body size of the species
        :param population: population size of the species
        :param traits: list of Traits belonging to this species, the list cannot contain duplicates
        :param fat_food: number of food tokens stored on the fat tissue trait, if the species has one
        """
        self.food = food if food is not None else self.DEFAULT_FOOD
        self.body = body if body is not None else self.DEFAULT_BODY
        self.population = population if population is not None else self.DEFAULT_POPULATION
        self.fat_food = fat_food if fat_food is not None else self.DEFAULT_FAT_FOOD
        self.traits = traits.copy() if traits is not None else []

    def __repr__(self):
        traits_repr = "[{}]".format(", ".join([repr(trait) for trait in self.traits]))
        arguments = [self.food, self.body, self.population, traits_repr]

        if Trait.FAT_TISSUE in self.traits and self.fat_food > self.DEFAULT_FAT_FOOD:
            arguments.append(self.fat_food)
            return "Species(food={}, body={}, population={}, traits={}, fat_food={})".format(*arguments)
        else:
            return "Species(food={}, body={}, population={}, traits={})".format(*arguments)

    def __str__(self):
        return self.__repr__()

    def __eq__(self, other):
        return isinstance(other, self.__class__) and (
                self.food == other.food and
                self.population == other.population and
                self.body == other.body and
                self.fat_food == other.fat_food and
                self.traits == other.traits
            )

    def is_attackable(self, attacker, left=None, right=None):
        """ Determine whether this species is attackable by the attacker species, given this species'
          left and right neighbors.
        :param attacker: the Species who is attacking
        :param left: left neighbor of this species or None
        :param right: right neighbor of this species or None
        :return: true if this species is attackable by the attacker, else false
        """
        prevent_attack_conditions = [
            # warning call
            lambda: (((left and left.has_trait(Trait.WARNING_CALL)) or
                     (right and right.has_trait(Trait.WARNING_CALL))) and
                     not attacker.has_trait(Trait.AMBUSH)),
            # other traits
            lambda: (self.has_trait(Trait.BURROWING) and self.food == self.population),
            lambda: (self.has_trait(Trait.CLIMBING) and not attacker.has_trait(Trait.CLIMBING)),
            lambda: (self.has_trait(Trait.HARD_SHELL) and (attacker.attacking_body - self.body) < HARD_SHELL_THRESHOLD),
            lambda: (self.has_trait(Trait.HERDING) and attacker.population <= self.population),
            lambda: (self.has_trait(Trait.SYMBIOSIS) and right and right.body > self.body),
        ]

        return not any(condition() for condition in prevent_attack_conditions)

    @property
    def attacking_body(self):
        """ Returns the body size of this species when it is attacking another species.
        :return: body size when attacking another species
        """
        return self.body + self.population if self.has_trait(Trait.PACK_HUNTING) else self.body

    def add_trait(self, trait):
        """ Add the given Trait to the species
        :param trait: trait to add to the species
        :raise: ValueError
        """
        if len(self.traits) == self.MAXIMUM_TRAITS:
            raise ValueError("A species can have at most {} traits.".format(self.MAXIMUM_TRAITS))
        self.traits.append(trait)

    def has_trait(self, trait):
        """ Returns True if this species has the given trait.
        :return: true if this species has the given trait
        """
        return trait in self.traits

    def replace_trait(self, slot, trait):
        """ Replaces the trait at the given slot by the given trait. If the existing trait is fat tissue
          any fat food stored is removed.
        :param slot: a number in [MINIMUM_TRAITS, MAXIMUM_TRAITS) pointing to the trait to replace
        :param trait: Trait to replace the existing trait with
        """
        current_trait = self.traits[slot]
        if current_trait == Trait.FAT_TISSUE:
            self.fat_food = self.MINIMUM_FAT_FOOD

        self.traits[slot] = trait

    def grow_population(self):
        """ Grows population of the species once.
          Effect: modifies the species population
        """
        self.population += self.POPULATION_GROWTH

    def grow_body(self):
        """ Grows body of the species once.
          Effect: modifies the species body
        """
        self.body += self.BODY_GROWTH

    def can_grow_population(self, n=1):
        """ Determines whether this species can add any more population.
        :param n: number times to grow
        :return: true if the species can add more population, false otherwise
        """
        return self.population + n * self.POPULATION_GROWTH <= self.MAXIMUM_POPULATION

    def can_grow_body(self, n=1):
        """ Determines whether this species can add any more population.
        :param n: number times to grow
        :return: true if the species can add more population, false otherwise
        """
        return self.body + n * self.BODY_GROWTH <= self.MAXIMUM_BODY

    def is_carnivore(self):
        """ Returns true if this species is a carnivore
        :return: true if this species is a carnivore
        """
        return self.has_trait(Trait.CARNIVORE)

    def is_scavenger(self):
        """ Returns true if this species is a scavenging species.
        :return: true if this species is a scanverger
        """
        return self.has_trait(Trait.SCAVENGER)

    def is_hungry(self):
        """ Returns true if this species is hungry
        :return: true if this species is hungry else false
        """
        return self.population > self.food

    def is_extinct(self):
        """ Returns true if this species is extinct. A species becomes extinct when its population reaches the minimum
          allowed population.
        :return: true if this species is extinct
        """
        return self.population <= self.MINIMUM_POPULATION

    def can_store_fat_food(self):
        """ Returns true if the species has the fat tissue trait and can store more food on its fat tissue card.
        :return: true if the species can store more food on fat tissue
        """
        return self.has_trait(Trait.FAT_TISSUE) and self.fat_food < self.body

    def feed_one(self, watering_hole):
        """ Attempts to feed this species one bite of food from the watering hole. The species will only be fed
          if it's hungry and enough tokens are available.
        :param watering_hole: number of tokens available in the watering hole
        :return: number of food tokens used
        """
        if self.is_hungry() and watering_hole >= self.BITE_SIZE:
            self.food += self.BITE_SIZE
            return self.BITE_SIZE
        return 0

    def feed(self, watering_hole):
        """ Attempts to perform a feeding action on the species. The feeding takes into account traits and will
          only be performed if the species is hungry and enough tokens are available.
        :param watering_hole: number of tokens available in the watering hole
        :return: (tokens used, times fed, has cooperation) tuple
        """
        tokens_used = self.feed_one(watering_hole)

        if self.has_trait(Trait.FORAGING):
            tokens_used += self.feed_one(watering_hole - tokens_used)

        times_fed = tokens_used // self.BITE_SIZE
        return tokens_used, times_fed, self.has_trait(Trait.COOPERATION)

    def auto_traits(self, player, species_idx, watering_hole):
        """ Activates the auto traits and determines whether the species has long neck
        :param player: owner of the species
        :param species_idx: index of this species in the owner's list
        :param watering_hole: number of tokens left in the watering_hole
        :return: true if this species has long neck
        """
        tokens_used = 0
        if self.has_trait(Trait.FERTILE) and self.can_grow_population():
            self.grow_population()
        if self.has_trait(Trait.LONG_NECK):
            tokens_used = player.feed_species(species_idx, watering_hole)
        self.move_fat_tissue()
        return tokens_used

    def store_fat(self, food_tokens):
        """ Stores the given number of food tokens on the fat tissue trait, the species must be able to store
          the given number of tokens.
        :param food_tokens: number of food tokens to store
        """
        self.fat_food += food_tokens

    def move_fat_tissue(self):
        """ Moves as much fat tissue as possible from the fat tissue storage to food.
        """
        food_need = self.population - self.food
        tokens_to_transfer = min(self.fat_food, food_need)
        self.food += tokens_to_transfer
        self.fat_food -= tokens_to_transfer

    def hurt(self, damage):
        """ Removes `damage' population from this species. If the species has more food than
          population after it is hurt, the food will be decreased appropriately.
        :param damage: damage to inflict to the population of this species
        :return: (extinct, has horns) tuple
        """
        self.population -= damage
        if self.food > self.population:
            self.food = self.population
        return self.is_extinct(), self.has_trait(Trait.HORNS)

    def end_turn(self):
        """ Performs the end of turn action on this species.
          * reduces the population to the number of food tokens
          * if species is not extinct, removes the food tokens and returns their number
        Effect: modifies population and food
        :return: (extinct, food tokens to store in bag) tuple, if extinct is true, food tokens value is meaningless
        """
        self.population = min(self.food, self.population)
        if self.is_extinct():
            return True, None

        food_tokens = self.food
        self.food = self.MINIMUM_FOOD
        return False, food_tokens

    def serialize(self):
        """ Returns a JSON-compatible representation of the Species
        :return: JSONSpecies
        """
        data = [
            [DataDefinitions.SPECIES_JSON_KEY_FOOD, self.food],
            [DataDefinitions.SPECIES_JSON_KEY_BODY, self.body],
            [DataDefinitions.SPECIES_JSON_KEY_POPULATION, self.population],
            [DataDefinitions.SPECIES_JSON_KEY_TRAITS, [trait.value for trait in self.traits]],
        ]

        if Trait.FAT_TISSUE in self.traits and self.fat_food > self.DEFAULT_FAT_FOOD:
            data.append([DataDefinitions.SPECIES_JSON_KEY_FAT_FOOD, self.fat_food])

        return data

    @classmethod
    def deserialize(cls, data):
        """ Creates an instance of Species from JSONSpecies, if the data is not a valid JSONSpecies
          raises an exception.
        :param data: JSONSpecies
        :return: Species
        :raise: ValueError
        """
        [_, food], [_, body], [_, population], [_, traits], *maybe_fat_food = data

        traits = [Trait(t) for t in traits]
        _, fat_food = maybe_fat_food[0] if maybe_fat_food else (None, None)

        return cls(food=food, body=body, population=population, traits=traits, fat_food=fat_food)

    def display(self):
        """ Returns a data representation of the species that can be used in a view
        :return: data representation of a species to be used in a view
        """
        data = {
            self.DISPLAY_KEY_FOOD: self.food,
            self.DISPLAY_KEY_BODY: self.body,
            self.DISPLAY_KEY_POPULATION: self.population,
            self.DISPLAY_KEY_TRAITS: [trait.value for trait in self.traits],
        }

        if Trait.FAT_TISSUE in self.traits and self.fat_food > self.DEFAULT_FAT_FOOD:
            data[self.DISPLAY_KEY_FAT_FOOD] = self.fat_food

        return data
