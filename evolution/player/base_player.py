"""
    Implements the base player for the Evolution game. The base implements basic functions
    relating to species, such as which species are hungry and the positional relations among
    species.

"""

from ..common.species import Species
from ..common.trait import Trait
from ..common.feeding_outcome import CarnivoreFeeding, VegetarianFeeding, FatTissueFeeding


class BasePlayer:
    """ Represent a base player with basic species operations.
    """

    def __init__(self, species=None):
        """ Creates a new BasePlayer with the given species
        :param species: list of species owned by the player
        """
        self.species = species.copy() if species is not None else []

    def __repr__(self):
        species = [repr(species) for species in self.species]
        return "BasePlayer(species={})".format(species)

    def __str__(self):
        return self.__repr__()

    def serialize(self):
        """ Returns a JSON-compatible representation of the BasePlayer
        :return: JSON-compatible representation of the player
        """
        return [species.serialize() for species in self.species]

    @classmethod
    def deserialize(cls, data):
        """ Creates a BasePlayer from its JSON representation as returned by serialize
        :return: Player object
        """
        species = [Species.deserialize(species) for species in data]
        return cls(species=species)

    def get_neighbors(self, species_index):
        """ Find the left and right neighbor of the given species. The given species
          must belong to this player. If the left or right neighbors do not exist,
          None will be returned in their place.
        :param species_index: index of the species to find the neighbors of
        :return: a tuple of left, right species, where the species is None if there
                 is no neighbor
        """
        left = self.species[species_index - 1] if species_index > 0 else None
        right = self.species[species_index + 1] if species_index < len(self.species) - 1 else None
        return left, right

    def get_hungry_species(self):
        """ Returns all hungry species belonging to this player
        :return: all hungry species belonging to this player
        """
        return [species for species in self.species if species.is_hungry()]

    def get_hungry_carnivores(self):
        """ Returns all hungry carnivores belonging to this player
        :return: all hungry carnivores belonging to this player
        """
        hungry_species = self.get_hungry_species()
        return [species for species in hungry_species if species.has_trait(Trait.CARNIVORE)]

    def get_species_index(self, species):
        """ Returns the index of the given species in the list of this player's species.
          The comparison is by reference, so the correct species is returned, instead of the first
          equal species.
        :param: species object to return the index of, must be part of self.species
        """
        for index, s in enumerate(self.species):
            if s is species:
                return index

    def get_possible_vegetarian_feedings(self):
        """ Returns all possible vegetarian feeding outcomes for this player
        :return: list of all possible vegetarian feedings
        """
        return [VegetarianFeeding(index) for index, species in enumerate(self.species)
                if not species.is_carnivore() and species.is_hungry()]

    def get_possible_fat_tissue_feedings(self, watering_hole, include_suboptimal=False):
        """ Returns all possible feeding outcomes from this player's species attacking any of the given player's
            species.
        :param watering_hole: number of tokens remaining in the watering hole, must be > 0
        :param include_suboptimal: if true also returns suboptimal feedings, that is feedings that request fewer
                                   tokens than the maximum amount
        :return: list of all possible carnivore feedings
        """
        feedings = []
        for index, species in enumerate(self.species):
            if not species.can_store_fat_food():
                continue

            food_tokens = min(watering_hole, species.body - species.fat_food)
            if not include_suboptimal:
                feedings.append(FatTissueFeeding(index, food_tokens))
            else:
                feedings.extend([FatTissueFeeding(index, tokens) for tokens in range(1, food_tokens + 1)])

        return feedings

    def get_possible_carnivore_feedings(self, players):
        """ Returns all possible feeding outcomes from this player's species attacking any of the given player's
            species.
        :param players: list of other players in the game
        :return: list of all possible carnivore feedings
        """

        feedings = []
        hungry_carnivores = self.get_hungry_carnivores()
        for carnivore in hungry_carnivores:
            carnivore_index = self.get_species_index(carnivore)
            for player_index, player in enumerate(players):
                for target in player.get_attackable_species(carnivore):
                    target_index = player.get_species_index(target)
                    feedings.append(CarnivoreFeeding(carnivore_index, player_index, target_index))

        return feedings

    def get_attackable_species(self, attacker):
        """ Returns all species that are attackable by the given species.
        :param attacker: attacking species
        :return: largest attackable species or None if there are no species
        """
        attackable_species = []
        for species_idx, species in enumerate(self.species):
            left, right = self.get_neighbors(species_idx)
            if species is not attacker and species.is_attackable(attacker, left=left, right=right):
                attackable_species.append(species)

        return attackable_species
