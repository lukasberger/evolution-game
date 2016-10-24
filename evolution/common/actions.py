"""

    Implements Action4 and its individual subactions.

"""

from itertools import chain
from collections import Counter

from .species import Species


class Actions:
    """ Represents Action4: the actions a player wants to perform during step 4 of a turn.

    An Action4 is [Natural, [GrowPopulation, ...], [GrowBody, ...], [BoardTransfer, ...] [ReplaceTrait, ...]].
    Interpretation: Every natural number in an Action4 represent an index into a sequence of species boards or cards.
    Constraints: The embedded arrays may be empty.
    """

    def __init__(self, discard, grow_population=None, grow_body=None, board_transfer=None, replace_trait=None):
        """
        :param discard: index of the card to discard
        :param grow_population: list of GrowPopulation
        :param grow_body: list of GrowBody actions
        :param board_transfer: list of BoardTransfer actions
        :param replace_trait: list of ReplaceTrait actions
        """
        self.discard = discard
        self.grow_population = grow_population if grow_population is not None else []
        self.grow_body = grow_body if grow_body is not None else []
        self.board_transfer = board_transfer if board_transfer is not None else []
        self.replace_trait = replace_trait if replace_trait is not None else []

    def validate(self, player):
        """ Validates the requested actions based on the given player state
        :param player: player state
        :return: true if the actions are valid else false
        """
        try:
            available_cards = len(player.cards)
            available_cards_set = set(range(available_cards))
            used_cards = self.used_cards()
            used_cards_set = set(used_cards)

            assert len(used_cards) == len(used_cards_set), "card used multiple times"
            assert used_cards_set.issubset(available_cards_set), "card out of range"

            assert BoardTransfer.validate(player, self)
            assert GrowPopulation.validate(player, self)
            assert GrowBody.validate(player, self)
            assert ReplaceTrait.validate(player, self)

        except AssertionError:
            return False

        return True

    def apply(self, player):
        """ Applies all actions stored in this Actions object to the given player.
          Effect: removes used cards from the player
        :param player: player to apply the actions to
        :return: value of the discarded card
        """
        for bt in self.board_transfer:
            bt.apply(player)

        for gp in self.grow_population:
            gp.apply(player)

        for gb in self.grow_body:
            gb.apply(player)

        for rt in self.replace_trait:
            rt.apply(player)

        discard_value = player.cards[self.discard].value

        used_cards = self.used_cards()
        player.remove_cards(used_cards)

        return discard_value

    def serialize(self):
        """ Returns the representation of this Actions as Action4 JSON
        :return: representation of this action as JSON
        """
        return [
            self.discard,
            [gp.serialize() for gp in self.grow_population],
            [gb.serialize() for gb in self.grow_body],
            [bt.serialize() for bt in self.board_transfer],
            [rt.serialize() for rt in self.replace_trait],
        ]

    @classmethod
    def deserialize(cls, data):
        """ Create a new Actions from Action4 JSON
        :param data: data to deserialize from
        :return: Actions
        """
        discard, gp, gb, bt, rt = data
        grow_population = [GrowPopulation.deserialize(x) for x in gp]
        grow_body = [GrowBody.deserialize(x) for x in gb]
        board_transfer = [BoardTransfer.deserialize(x) for x in bt]
        replace_trait = [ReplaceTrait.deserialize(x) for x in rt]

        return cls(discard, grow_population, grow_body, board_transfer, replace_trait)

    def used_cards(self):
        """ Returns the list of all indices of cards used in the actions
        """
        used_cards = [self.discard]
        actions = [self.grow_population, self.grow_body, self.board_transfer, self.replace_trait]
        for action_list in actions:
            used_cards.extend(chain.from_iterable(a.used_cards() for a in action_list))
        return used_cards


class Action:
    """ Represents a part of actions4 """

    @staticmethod
    def extract_actions(action4):
        """ Returns the appropriate actions stored in the given action4 object.
        :param action4: action4 object to extract the actions from
        :return: list of Action
        """
        raise NotImplementedError("This method must be implemented by a subclass.")

    @classmethod
    def validate(cls, player, action4):
        """ Validates the given list of Actions in the context of player and action4
        :param player: player who requested the actions
        :param action4: action4 object
        :return: True if the actions are valid
        """
        actions = cls.extract_actions(action4)
        valid_individual = all(a.validate_individual(player, action4) for a in actions)
        return valid_individual and cls.validate_in_context(actions, player, action4)

    def validate_individual(self, player, action4):
        """ Validates this action in the context of player and action4
        :param player: player who requested the actions
        :param action4: action4 object
        :return: True if this action are valid
        """
        raise NotImplementedError("This method must be implemented by a subclass.")

    @classmethod
    def validate_in_context(cls, actions, player, action4):
        """ Validates this action in the context of player, action4 and other actions of the same type.
        :param actions: list of Actions to validate
        :param player: player who requested the actions
        :param action4: action4 object
        :return: True if this action are valid
        """
        raise NotImplementedError("This method must be implemented by a subclass.")

    def apply(self, player):
        """ Applies the action on the given player
        :param player: player to apply the action to
        """
        raise NotImplementedError("This method must be implemented by a subclass.")

    def serialize(self):
        """ Returns the representation of this action
        :return: representation of this action as JSON
        """
        raise NotImplementedError("This method must be implemented by a subclass.")

    @classmethod
    def deserialize(cls, data):
        """ Deserializes the given action
        :param data: JSON-formatted Action
        :return: deserailized Action
        """
        raise NotImplementedError("This method must be implemented by a subclass.")

    def used_cards(self):
        """ Returns the list of all indices of cards used in the actions
        """
        raise NotImplementedError("This method must be implemented by a subclass.")


class SpeciesAction(Action):
    """ Baseclass for all Actions that can be performed on an individual species """

    def __init__(self, species_index):
        """ Creates a new SpeciesAction
        :param species_index: index of the species to perform the action on
        """
        self.species_index = species_index

    def validate_individual(self, player, action4):
        # species index must be within current species + new species
        available_species = len(player.species) + len(action4.board_transfer)
        return 0 <= self.species_index < available_species  # "species index out of range"


class GrowAction(SpeciesAction):
    """ Represents a grow body or grow population action """

    NAME = None

    def __init__(self, species_index, card_index):
        """
        :param card_index: index of the card to use to perform the grow action
        """
        super().__init__(species_index)
        self.card_index = card_index

    @staticmethod
    def get_grow_counter(actions):
        """ Returns a counter representing how many times each action was applied to a species index
        :param actions: list of GrowAction
        """
        return Counter(ga.species_index for ga in actions)

    def serialize(self):
        return [self.NAME, self.species_index, self.card_index]

    @classmethod
    def deserialize(cls, data):
        _, species_index, card_index = data
        return cls(species_index, card_index)

    def used_cards(self):
        return [self.card_index]


class GrowPopulation(GrowAction):
    """
    a GrowPopulation is ["population",Natural, Natural].
    Interpretation: A ["population",i,j] array requests a trade of card j for a growth of the population of species
        board i by one.
    """

    NAME = "population"

    @staticmethod
    def extract_actions(action4):
        return action4.grow_population

    @classmethod
    def validate_in_context(cls, actions, player, action4):
        # context restriction: after all grow population actions are applied the species's population must be within
        # bounds
        existing_species_count = len(player.species)
        population_grow_counter = cls.get_grow_counter(actions)
        for species_index, grow_amount in population_grow_counter.items():
            target_species = player.species[species_index] if species_index < existing_species_count else Species()
            if not target_species.can_grow_population(grow_amount):
                return False
        return True

    def apply(self, player):
        player.species[self.species_index].grow_population()


class GrowBody(GrowAction):
    """
    A GrowBody is ["body",Natural, Natural].
    Interpretation: A ["body",i,j] array requests a trade of card j for a growth of the body of species
        board i by one.
    """

    NAME = "body"

    @staticmethod
    def extract_actions(action4):
        return action4.grow_body

    @classmethod
    def validate_in_context(cls, actions, player, action4):
        # context restriction: after all grow body actions are applied the species's body must be within bounds
        existing_species_count = len(player.species)
        body_grow_counter = cls.get_grow_counter(actions)
        for species_index, grow_amount in body_grow_counter.items():
            target_species = player.species[species_index] if species_index < existing_species_count else Species()
            if not target_species.can_grow_body(grow_amount):
                return False
        return True

    def apply(self, player):
        player.species[self.species_index].grow_body()


class BoardTransfer(Action):
    """
    A BoardTransfer is one of:
    [Natural]
    [Natural, Natural]
    [Natural, Natural, Natural]
    [Natural, Natural, Natural, Natural]

    Interpretation: A BoardTransfer represents a species board addition to the right of the existing sequence of
        boards for the corresponding player. Specifically, [i, j, ..., k] uses the first of the player’s cards (i) to
        "pay" for the new board and uses the remaining (up to three) cards (j, ..., k) as traits.
        Constraint Once a player has added a species board, it becomes impossible to add a trait.
    """

    def __init__(self, card_index, trait_card_indices):
        """
        :param card_index: card index to use to create the species
        :param trait_card_indices: list of card indices of the cards whose traits should be added to the new species
        """
        self.card_index = card_index
        self.trait_card_indices = trait_card_indices

    @staticmethod
    def extract_actions(action4):
        return action4.board_transfer

    def validate_individual(self, player, action4):
        traits = self.get_traits(player)
        return len(set(traits)) == len(traits)  # "no duplicate traits allowed"

    def get_traits(self, player):
        """ Returns the traits that should be added to the new species based on the player's hand """
        return [player.cards[idx].trait for idx in self.trait_card_indices]

    @classmethod
    def validate_in_context(cls, actions, player, action4):
        return True  # board transfer doesn't have any context restrictions

    def apply(self, player):
        traits = [player.cards[idx].trait for idx in self.trait_card_indices]
        player.add_species(traits=traits)

    def serialize(self):
        return [self.card_index] + self.trait_card_indices

    @classmethod
    def deserialize(cls, data):
        card_index, *trait_card_indices = data
        return cls(card_index, trait_card_indices)

    def used_cards(self):
        return [self.card_index] + self.trait_card_indices


class ReplaceTrait(SpeciesAction):
    """
    An ReplaceTrait is [Natural, Natural, Natural].
    Interpretation: A ReplaceTrait represents a trait replacement for a species board. Specifically, [b, i, j]
        specifies that board b’s i’s trait card is replaced with the j’s card from the player’s card sequence.
    """

    def __init__(self, species_index, trait_slot, card_index):
        """
        :param species_index: index of the species whose trait should be replaced
        :param trait_slot: slot number of the trait to replace
        :param card_index: card index of the card to add as the replacement trait
        """
        super().__init__(species_index)
        self.trait_slot = trait_slot
        self.card_index = card_index

    @staticmethod
    def extract_actions(action4):
        return action4.replace_trait

    def validate_individual(self, player, action4):
        valid_species_index = super().validate_individual(player, action4)
        original_species_len = len(player.species)

        if not valid_species_index:
            return False

        if self.species_index < original_species_len:
            species = player.species[self.species_index]
            valid_trait_slot = self.trait_slot < len(species.traits)
        # the target species is newly added, check that the newly added species has the trait slot occupied
        else:
            board_transfer = action4.board_transfer[self.species_index - original_species_len]
            valid_trait_slot = self.trait_slot < len(board_transfer.trait_card_indices)

        return valid_trait_slot

    @classmethod
    def validate_in_context(cls, actions, player, action4):
        # context restriction: no species may have duplicate traits after all replace trait actions are applied
        species_traits = [species.traits.copy() for species in player.species]
        species_traits.extend([bt.get_traits(player) for bt in action4.board_transfer])
        for rt in actions:
            trait = player.cards[rt.card_index].trait
            species_traits[rt.species_index][rt.trait_slot] = trait

        return all(len(set(traits)) == len(traits) for traits in species_traits)

    def apply(self, player):
        species = player.species[self.species_index]
        card = player.cards[self.card_index]
        species.replace_trait(self.trait_slot, card.trait)

    def serialize(self):
        return [self.species_index, self.trait_slot, self.card_index]

    @classmethod
    def deserialize(cls, data):
        species_index, trait_slot, card_index = data
        return cls(species_index, trait_slot, card_index)

    def used_cards(self):
        return [self.card_index]
