"""
    Implements a dummy Player.

"""

from .base_player import BasePlayer
from .external_player import ExternalPlayer

from ..common.species import Species
from ..common.trait_card import TraitCard
from ..common.feeding_outcome import VegetarianFeeding, FatTissueFeeding, CarnivoreFeeding, NoFeeding, CannotFeed


class DummyPlayer(BasePlayer, ExternalPlayer):
    """ Represents a Player with a dummy strategy. """

    def __init__(self, idx=None, species=None, cards=None, bag=None):
        """ Creates a new DummyPlayer
        :param idx: id of the player
        :param species: list of species owned by this player
        :param cards: list of cards in this player's hand
        :param bag: number of tokens in this player's bag
        """
        super().__init__(species=species)
        self.idx = idx
        self.cards = cards.copy() if cards is not None else []
        self.bag = bag

    def __repr__(self):
        return "Dummy" + super().__repr__()

    def update_state(self, player_state):
        """ Updates the player's state given its PlayerState
        :param player_state: PlayerState as defined in ExternalPlayer
        """
        species, bag, cards = player_state
        self.bag = bag
        self.species = [Species.deserialize(s) for s in species]
        self.cards = [TraitCard.deserialize(c) for c in cards]

    def start(self, watering_hole, player_state):
        """ Called at the beginning of a turn, defined in ExternalPlayer """
        # watering hole is ignored because dummy player has no use for it
        self.update_state(player_state)

    def feed_next(self, player_state, players, watering_hole):
        """ Determines the next species to be fed. The watering_hole must not be empty. The player choose a species
          to feed in the following way:
            1) one of its own species with the fat-tissue trait and the number of tokens it wishes to store
            2) one of its own vegetarian species
            3) one of its own carnivores plus a different player and one of this player’s species
            4) an indication that it does not wish to feed any species anymore.

            Parameters and return type described in ExternalPlayer.
        """
        self.update_state(player_state)
        players = [self.deserialize(p) for p in players]

        fat_tissue_species = [species for species in self.species if species.can_store_fat_food()]
        hungry_vegetarians = self.get_hungry_vegetarians()
        hungry_carnivores_can_attack_others = self.get_hungry_carnivores_can_attack(players)
        hungry_carnivores_can_attack_own = self.get_hungry_carnivores_can_attack([self])

        if fat_tissue_species:
            feeding_outcome = self.feed_fat_tissue(fat_tissue_species, watering_hole)
        elif hungry_vegetarians:
            feeding_outcome = self.feed_vegetarian(hungry_vegetarians)
        elif hungry_carnivores_can_attack_others:
            feeding_outcome = self.feed_carnivore(hungry_carnivores_can_attack_others, players)
        elif hungry_carnivores_can_attack_own:
            feeding_outcome = NoFeeding()
        else:
            feeding_outcome = CannotFeed()

        return feeding_outcome.serialize()

    def choose(self, preceding, following):
        """ Chooses the appropriate actions for the silly strategy.
        Signature described in ExternalPlayer.
        """
        # it uses cards in <-card order.
        sorted_card_with_indices = sorted(enumerate(self.cards), key=lambda index_card: index_card[1])
        indices_in_order = [index for index, card in sorted_card_with_indices]

        # the first card goes toward food.
        discard = indices_in_order.pop(0)
        gp, gb, bt, rt = [], [], [], []

        # With the next two cards, it asks for an additional species board with one trait.
        bt.append([indices_in_order.pop(0), indices_in_order.pop(0)])

        # If there are cards left:
        new_species_index = len(self.species)
        # it grows the population and body of the added species and
        if indices_in_order:
            gp.append(["population", new_species_index, indices_in_order.pop(0)])
        if indices_in_order:
            gb.append(["body", new_species_index, indices_in_order.pop(0)])

        # replaces the one trait of the new species board.
        if indices_in_order:
            rt.append([new_species_index, 0, indices_in_order.pop(0)])

        return [discard, gp, gb, bt, rt]

    @staticmethod
    def get_max_values(values, key):
        """ Return all maximum values from the list of values based on the given key function.
        :param values: nonempty list of values
        :param key: function that generates a key
        :return: list of maximum values according to the key function
        """
        max_key = max(key(value) for value in values)
        return [value for value in values if key(value) == max_key]

    @staticmethod
    def species_ordering_key(species):
        """ Sorting key used to order species by increasing population, increasing food,
          and increasing body size.
        :param species: species object
        :return: ordering key
        """
        return species.population, species.food, species.body

    @classmethod
    def order_species(cls, species_subset):
        """ Orders the given subset of this player's species lexicographically
        :param species_subset: subset of this player's species
        :return: ordered species
        """
        # reverse because sorted sorts smallest to largest
        return sorted(species_subset, key=cls.species_ordering_key, reverse=True)

    def feed_fat_tissue(self, fat_tissue_species, watering_hole):
        """ Given a list of non-fat-satisfied species, feed the one with the largest need with as many tokens
          as possible.
        :param fat_tissue_species: list of species who can store more fat food
        :param watering_hole: number of tokens in the watering hole
        :return: FeedingOutcome
        """
        def fat_need(species):
            return species.body - species.fat_food

        species_with_greatest_need = self.get_max_values(fat_tissue_species, key=fat_need)

        species_to_feed = self.order_species(species_with_greatest_need)[0]
        food_tokens = min(watering_hole, fat_need(species_to_feed))
        return FatTissueFeeding(self.leftmost_species_index(species_to_feed), food_tokens)

    def feed_vegetarian(self, hungry_vegetarians):
        """ Feed the largest species from the given list of hungry vegetarians.
        :param hungry_vegetarians: list of hungry vegetarian species
        :return: FeedingOutcome
        """
        species_to_feed = self.order_species(hungry_vegetarians)[0]
        return VegetarianFeeding(self.leftmost_species_index(species_to_feed))

    def feed_carnivore(self, hungry_carnivores, players):
        """ Given a list of hungry carnivores that have at least one valid target, feed the largest carnivore by
          attacking the largest species it can attack from one of the given players.
        :param hungry_carnivores: list of hungry carnivores with at least one valid target belonging to one of players
        :param players: other players in the game
        :return: FeedingOutcome
        """
        attacker = self.order_species(hungry_carnivores)[0]

        largest_attackable_species_list = [player.get_largest_attackable_species(attacker) for player in players]
        largest_attackable_species = max(filter(None, largest_attackable_species_list), key=self.species_ordering_key)

        defending_player_index = largest_attackable_species_list.index(largest_attackable_species)
        defending_player = players[defending_player_index]

        return CarnivoreFeeding(self.leftmost_species_index(attacker),
                                defending_player_index,
                                defending_player.leftmost_species_index(largest_attackable_species))

    def get_largest_attackable_species(self, attacker):
        """ Returns the largest species that is attackable by the given species.
        :param attacker: attacking species
        :return: largest attackable species or None if there are no species
        """
        attackable_species = self.get_attackable_species(attacker)
        ordered_species = self.order_species(attackable_species)
        return ordered_species[0] if len(ordered_species) > 0 else None

    def leftmost_species_index(self, species):
        """ Returns the index of the leftmost species equal to the given species. The given species
          must be owned by this player.
        :param species: species to find the index of
        :return: index of the leftmost species equal to the given species
        """
        return self.species.index(species)

    def get_hungry_vegetarians(self):
        """ Returns all hungry vegetarians belonging to this player
        :return: all hungry vegetarians belonging to this player
        """
        hungry_species = self.get_hungry_species()
        return [species for species in hungry_species if not species.is_carnivore()]

    def get_hungry_carnivores_can_attack(self, players):
        """ Returns all hungry carnivores belonging to this player that have at least one valid target among the
          other players' species.
        :return: all hungry carnivores belonging to this player that have at least one valid target
        """
        hungry_carnivores_with_targets = self.get_hungry_carnivores_with_targets(players)
        return [carnivore for carnivore, _ in hungry_carnivores_with_targets]

    def get_hungry_carnivores_with_targets(self, players):
        """ Returns all hungry carnivores belonging to this player that have at least one valid target among the
          other players' species.
        :return: a tuple of (hungry carnivore, valid targets), where valid targets is a list of lists of attackable
                 species for each given player, each returned carnivore has at least one valid target
        """
        hungry_carnivores = self.get_hungry_carnivores()
        hungry_carnivores_with_targets = []
        for carnivore in hungry_carnivores:
            attackable_list = [player.get_attackable_species(carnivore) for player in players]
            if any(attackable_list):
                hungry_carnivores_with_targets.append((carnivore, attackable_list))
        return hungry_carnivores_with_targets
