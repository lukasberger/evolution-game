"""
    Contains classes for all possible outcomes for the Player's feed species method.

    A FeedingOutcome is one of:
        NoFeeding
        VegetarianFeeding
        FatTissueFeeding
        CarnivoreFeeding
        CannotFeed

"""


class FeedingOutcome:
    """ Base feeding outcome class. Each feeding outcome must overwrite the given methods.
    """

    def serialize(self):
        """ Returns a JSON-friendly representation of the feeding outcome.
        :return: JSON-friendly representation of the outcome
        """
        raise NotImplementedError("The base feeding outcome cannot be serialized.")

    def validate(self, dealer):
        """ Validates the feeding given the current dealer state.
        :param dealer: a Dealer object representing the state of the game
        :return: true if the feeding is valid, otherwise false
        """
        raise NotImplementedError("The base feeding outcome cannot be validated.")

    def apply(self, dealer):
        """ Effect: mutates the given dealer according to the results of the feeding.
        :param dealer: a Dealer object representing the state of the game
        :return: true if the player should be removed after feeding else false
        """
        raise NotImplementedError("The base feeding outcome cannot be validated.")

    @classmethod
    def deserialize(cls, data):
        """ Deserializes a Feeding into the corresponding FeedingOutcome. If the given feeding outcome
          is not one of the defined Feedings, the result will be CannotFeed
        :param data: serialized Feeding
        :return: FeedingOutcome
        """
        if data is False:
            return NoFeeding()
        if isinstance(data, int):
            return VegetarianFeeding(data)
        if isinstance(data, list) and len(data) == 2:
            return FatTissueFeeding(*data)
        if isinstance(data, list) and len(data) == 3:
            return CarnivoreFeeding(*data)
        return CannotFeed()


class SpeciesFeedingOutcome(FeedingOutcome):
    """ Represents a feeding outcome where one of the player's species is involved.
    """

    def __init__(self, species_index):
        """ Creates a new species feeding outcome
        :param species_index: index of the species to feed in the Player's list of species
        """
        self.species_index = species_index

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.species_index == other.species_index

    def serialize(self):
        raise NotImplementedError("A species feeding outcome must be subclassed.")

    def validate(self, dealer):
        raise NotImplementedError("A species feeding outcome must be subclassed.")

    def apply(self, dealer):
        raise NotImplementedError("A species feeding outcome must be subclassed.")


class VegetarianFeeding(SpeciesFeedingOutcome):
    """ Represents a player's choice to feed a vegetarian species.

    JSON: Natural
    Meaning: the index of a single species that is vegetarian and gets the next token of food;

    """

    def serialize(self):
        return self.species_index

    def validate(self, dealer):
        current_player = dealer.get_current_player()
        return self in current_player.get_possible_vegetarian_feedings()

    def apply(self, dealer):
        current_player = dealer.get_current_player()
        dealer.feed_species(current_player, self.species_index)
        return False


class FatTissueFeeding(SpeciesFeedingOutcome):
    """ Represents a player's choice to store food tokens on a species with fat tissue.

    JSON: [Natural, Nat]
    Meaning: an index to a given species and desired number of food tokens—meaning
        the indexed species comes with a fat-tissue trait and wishes to store the specified
        number of food tokens;

    """

    def __init__(self, species_index, food_tokens):
        """ Creates a new fat tissue feeding
        :param species_index: index of the species to feed in the Player's list of species
        :param food_tokens: number of food tokens the player intends to store
        """
        super(FatTissueFeeding, self).__init__(species_index)
        self.food_tokens = food_tokens

    def __eq__(self, other):
        return super().__eq__(other) and self.food_tokens == other.food_tokens

    def serialize(self):
        return [self.species_index, self.food_tokens]

    def validate(self, dealer):
        current_player = dealer.get_current_player()
        return self in current_player.get_possible_fat_tissue_feedings(dealer.watering_hole, include_suboptimal=True)

    def apply(self, dealer):
        # at this point if a fat tissue feeding is valid, the player request a valid number of
        # food tokens
        current_player = dealer.get_current_player()
        dealer.feed_species_fat_tissue(current_player, self.species_index, self.food_tokens)
        return False


class CarnivoreFeeding(SpeciesFeedingOutcome):
    """ Represents a player's choice to feed a carnivore by attacking another player's species

    JSON: [Natural, Natural, Natural]
    Meaning: an index pointing to a species of the current player,
        an index for an element of the given sequence of players, and an index for
        one of its species—meaning the first species attacks the second species,
        which belongs to the given player.

    """

    def __init__(self, species_index, player_index, defender_index):
        """ Creates a new carnivore feeding
        :param species_index: index of the carnivore species to feed in the Player's list of species
        :param player_index: index of the player who owns the species being attacked
        :param defender_index: index of the species being attack the the defending Player's list of species
        """
        super(CarnivoreFeeding, self).__init__(species_index)
        self.player_index = player_index
        self.defender_index = defender_index

    def __eq__(self, other):
        return (super().__eq__(other) and
                self.player_index == other.player_index and
                self.defender_index == other.defender_index)

    def serialize(self):
        return [self.species_index, self.player_index, self.defender_index]

    def validate(self, dealer):
        current_player = dealer.get_current_player()
        players = dealer.player_queue_all
        players = players[1:] + players[:1]
        return self in current_player.get_possible_carnivore_feedings(players)

    def apply(self, dealer):
        dealer.carnivore_feeding(self.species_index, self.player_index, self.defender_index)
        return False


class NoFeeding(FeedingOutcome):
    """ Represents the player's choice not to feed anyone.

    JSON: false
    Meaning: the player forgoes any additional chance to take food from the watering hole
        for a carnivore attack or a fat-tissue fill-up during this turn’s feeding cycle. Of course,
        if the player owns species that "scavenge", these species still receive food if a carnivore eats.

    """

    def __eq__(self, other):
        return isinstance(other, self.__class__)

    def serialize(self):
        return False

    def validate(self, dealer):
        return True

    def apply(self, dealer):
        return True


class CannotFeed(FeedingOutcome):
    """ Represents a player's inability to feed any of its species.

    JSON: cannot be represented
    Meaning: the player has no more feeding choices

    """

    def __eq__(self, other):
        return isinstance(other, self.__class__)

    def serialize(self):
        return None

    def validate(self, dealer):
        return True

    def apply(self, dealer):
        return True
