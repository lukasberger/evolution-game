"""
    Implements an Evolution player as seen by the Dealer. The Player objects keeps track of a player's state

"""
from .base_player import BasePlayer
from .dummy_player import DummyPlayer

from ..data_definitions import DataDefinitions, unpack

from ..common.feeding_outcome import CannotFeed, FeedingOutcome
from ..common.species import Species
from ..common.trait_card import TraitCard
from ..common.actions import Actions
from ..common.player_helpers import external_player_call, ExternalPlayerCall


class Player(BasePlayer):
    """ Represent an internal Player as seen by the Dealer.
    """

    DEFAULT_FOOD_BAG_VALUE = 0

    DATA_KEY_IDX = "id"
    DATA_KEY_BAG = "bag"
    DATA_KEY_SPECIES = "species"
    DATA_KEY_CARDS = "cards"

    def __init__(self, idx, species=None, bag=None, cards=None, external=None):
        """ Creates a Player with the specified ID
        :param idx: ID of the Player
        :param species: list of species owned by the player
        :param bag: number of food tokens in the Player's bag
        :param cards: list of TraitCards the player has
        :param external: external player associated with this internal player
        """
        super().__init__(species=species)
        self.idx = idx
        self.bag = bag if bag is not None else self.DEFAULT_FOOD_BAG_VALUE
        self.cards = cards.copy() if cards is not None else []
        self.external = external if external is not None else DummyPlayer()

    def __repr__(self):
        species = "[{}]".format(", ".join([repr(species) for species in self.species]))
        if self.cards:
            cards = "[{}]".format(", ".join([repr(card) for card in self.cards]))
            return "Player(idx={}, species={}, bag={}, cards={})".format(self.idx, species, self.bag, cards)
        else:
            return "Player(idx={}, species={}, bag={})".format(self.idx, species, self.bag)

    def __str__(self):
        return self.__repr__()

    def score(self):
        """ Returns the current score of the player, which is calculated as follows:
          score = bag + sum(population of existing species) + sum(trait cards for each species)
        :return: this player's score
        """
        return self.bag + sum(s.population for s in self.species) + sum(len(s.traits) for s in self.species)

    def add_cards(self, cards):
        """ Add the given list of cards to the player's cards
        :param cards: list of cards to add
        """
        self.cards.extend(cards)

    def to_player_state(self):
        """ Returns a PlayerState representation of this player as defined in ExternalPlayer
        :return: PlayerState representation of this player
        """
        species = [s.serialize() for s in self.species]
        cards = [c.serialize() for c in self.cards]
        return [species, self.bag, cards]

    @external_player_call()
    def start(self, watering_hole, new_species, cards):
        """ Sends a start message to the external player with the current state of self.
        :param watering_hole: number of food tokens available at the watering hole
        :param new_species: if True the player will receive a new species
        :param cards: list of cards this player was given
        :raise: ExternalPlayerIssue
        """
        if new_species:
            self.species.append(Species())
        self.add_cards(cards)

        with ExternalPlayerCall():
            self.external.start(watering_hole, self.to_player_state())

    def end_turn(self):
        """ Ends a turn. At the end of the turn the following happens:
          * all species' population is reduced to their food level
          * if the species go extinct, the player receives cards from the dealer and the species is removed
          * all food tokens are transferred from species boards to the bag
        :return: number of extinct species
        """
        extinct_species_indices = []

        for species_idx, species in enumerate(self.species):
            extinct, food = species.end_turn()

            if extinct:
                extinct_species_indices.append(species_idx)
            else:
                self.bag += food

        # remove species starting from the right to preserve species indices
        for species_idx in sorted(extinct_species_indices, reverse=True):
            self.species.pop(species_idx)

        return len(extinct_species_indices)

    @external_player_call()
    def choose(self, players):
        """ Asks the external player to choose the actions to take in steps 2 and 3 of the game.
          This includes choosing which card to discard.
        :param players: other players in the game
        :return: Actions object representing the player's chosen actions
        :raise: ExternalPlayerIssue
        """
        self_index = players.index(self)
        before = [[s.serialize() for s in p.species] for p in players[:self_index]]
        after = [[s.serialize() for s in p.species] for p in players[self_index + 1:]]

        with ExternalPlayerCall():
            action4 = self.external.choose(before, after)
            assert DataDefinitions.action4(action4), "invalid action4 returned by external player"
            return Actions.deserialize(action4)

    @external_player_call()
    def feeding_choice(self, players, watering_hole):
        """ Determines the next feeding choice for the player automatically if possible, or asks the player
          to make the choice. The possible outcomes are:
            * the player cannot feed any more species
            * it will automatically feed
                -- a single species with a non-full fat-food trait card (to the max possible)
                -- a single vegetarian
                -- a single carnivore that can attack only one species from a different player
                    (no self-attack is allowed).
            * there is more than one possibility and the player is asked to make a feeding choice
        :param players: other players in the game
        :param watering_hole: number of food tokens left in the watering hole
        :return: the next feeding choice for the player
        :raise: ExternalPlayerIssue
        """
        hungry_species = self.get_hungry_species()
        possible_vegetarian_feedings = self.get_possible_vegetarian_feedings()
        possible_fat_tissue_feedings = self.get_possible_fat_tissue_feedings(watering_hole)
        # list of hungry carnivores that have at least one valid target among any player's species
        possible_carnivore_feedings = self.get_possible_carnivore_feedings(players + [self])
        possible_carnivore_feedings_others = self.get_possible_carnivore_feedings(players)

        # there are no possible feedings if:
        # * there are no hungry species and no species that can store more fat tokens
        # * all hungry species are carnivores that have no targets and there are no species that can store more fat
        no_feedable_species = ((not hungry_species) or
                               (not possible_vegetarian_feedings and not possible_carnivore_feedings))
        if no_feedable_species and not possible_fat_tissue_feedings:
            return CannotFeed()

        # a single species with a non-full fat-food trait card
        if (len(possible_fat_tissue_feedings) == 1 and
                not possible_vegetarian_feedings and not possible_carnivore_feedings):
            return possible_fat_tissue_feedings[0]

        # a single vegetarian
        if (len(possible_vegetarian_feedings) == 1 and
                not possible_fat_tissue_feedings and not possible_carnivore_feedings):
            return possible_vegetarian_feedings[0]

        # a single carnivore
        if (len(possible_carnivore_feedings_others) == 1 and len(possible_carnivore_feedings) == 1 and
                not possible_fat_tissue_feedings and not possible_vegetarian_feedings):
            return possible_carnivore_feedings[0]

        # there is more than one feeding possibility
        players = [[s.serialize() for s in p.species] for p in players]

        with ExternalPlayerCall():
            feeding_outcome = self.external.feed_next(self.to_player_state(), players, watering_hole)
            assert DataDefinitions.feeding_outcome(feeding_outcome), "invalid feeding returned by external player"
            return FeedingOutcome.deserialize(feeding_outcome)

    def feed_species(self, species_index, watering_hole):
        """ Feeds the species at the given index based on the number of tokens available in the watering hole,
          taking the species traits into account.
        :param species_index: index of the species to feed
        :param watering_hole: number of food tokens available in the watering hole
        :return: number of food tokens consumed during the feeding
        """
        species = self.species[species_index]
        tokens_used, times_fed, cooperation = species.feed(watering_hole)

        if cooperation:
            for _ in range(0, times_fed):
                tokens_used += self.cooperate(species_index, watering_hole - tokens_used)

        return tokens_used

    def cooperate(self, species_index, watering_hole):
        """ Triggers cooperation for the species at the given index.
        :param species_index: index of the species to trigger cooperation for
        :param watering_hole: number of food tokens available in the watering hole
        :return: number of food tokens consumed during the feeding
        """
        right_neighbor_index = species_index + 1
        # check that the neighbor is in range
        if right_neighbor_index < len(self.species):
            return self.feed_species(right_neighbor_index, watering_hole)
        return 0

    def store_fat_tissue(self, species_index, food_tokens):
        """ Stores the given number of food tokens for the species at the given index as fat tissue.
        :param species_index: index of the species to store fat tissue for
        :param food_tokens: number of food tokens to store as fat tissue
        """
        species = self.species[species_index]
        species.store_fat(food_tokens)

    def hurt_species(self, species_index, damage):
        """ Kills off 'damage' population of the species at the given index.
          EFFECT: if the species goes extinct, it is removed
        :param species_index: index of the species to hurt
        :param damage: damage to inflict on the species population
        :return: (did species go extinct, does species have horns) tuple
        """
        species = self.species[species_index]
        extinct, horns = species.hurt(damage)

        if extinct:
            self.species.pop(species_index)

        return extinct, horns

    def scavenge(self, watering_hole):
        """ Called with the remaining tokens in the watering hole when any species in the game is fed.
        :param watering_hole: number of food tokens available in the watering hole
        :return: number of food tokens consumed
        """
        food_taken = 0
        for idx, species in enumerate(self.species):
            if species.is_scavenger():
                food_taken += self.feed_species(idx, watering_hole - food_taken)

        return food_taken

    def auto_traits(self, watering_hole):
        """ Effect: feeds all species in order, based on their auto-feeding traits
        :param watering_hole: number of food tokens in the watering hole
        :return: number of tokens consumed
        """
        food_taken = 0
        for species_idx, species in enumerate(self.species):
            food_taken += species.auto_traits(self, species_idx, watering_hole - food_taken)

        return food_taken

    def remove_cards(self, indices):
        """ Remove the cards at the given indices from the player's hand. The list must contain unique indices
            within the range of the player's cards.
          Effect: modifies the player's hand
        """
        card_indices = sorted(indices, reverse=True)
        for card_index in card_indices:
            self.cards.pop(card_index)

    def add_species(self, *args, **kwargs):
        """ Adds a new species board with the given attributes. Valid attributes are any attributes defined on Species.
        """
        species = Species(*args, **kwargs)
        self.species.append(species)

    def serialize(self):
        """ Returns a JSON-compatible representation of the Player
        :return: JSON-compatible representation of the player
        """
        serialized = [
            [DataDefinitions.PLAYER_JSON_KEY_IDX, self.idx],
            [DataDefinitions.PLAYER_JSON_KEY_SPECIES, [species.serialize() for species in self.species]],
            [DataDefinitions.PLAYER_JSON_KEY_BAG, self.bag],
        ]

        if self.cards:
            serialized.append([DataDefinitions.PLAYER_JSON_KEY_CARDS, [card.serialize() for card in self.cards]])

        return serialized

    @classmethod
    def deserialize(cls, data):
        """ Creates a Player from its JSON representation, raises an Exception
          if the data is invalid.
        :return: Player object
        """
        [_, idx], [_, species], [_, bag], *maybe_cards = data

        species = [Species.deserialize(s) for s in species]

        if maybe_cards:
            _, cards = maybe_cards[0]
            cards = [TraitCard.deserialize(card) for card in cards]
        else:
            cards = None

        return cls(idx=idx, species=species, bag=bag, cards=cards)

    def display(self):
        """ Returns a data representation of the player that can be used in a view
        :return: data representation of the player to be used in a view
        """
        return {
            self.DATA_KEY_IDX: self.idx,
            self.DATA_KEY_BAG: self.bag,
            self.DATA_KEY_SPECIES: [s.display() for s in self.species],
            self.DATA_KEY_CARDS: [tc.display() for tc in self.cards],
        }
