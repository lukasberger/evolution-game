"""

    Implements a game strategy for Evolution

"""

from .base_player import BasePlayer
from .external_player import ExternalPlayer

from ..common.species import Species
from ..common.trait_card import TraitCard
from ..common.trait import Trait
from ..common.feeding_outcome import NoFeeding


class StrategyPlayer(BasePlayer, ExternalPlayer):

    # ordered based on perceived value
    TRAIT_ORDERING = {
        Trait.CARNIVORE: 5,
        Trait.PACK_HUNTING: 4,
        Trait.AMBUSH: 3,
        Trait.CLIMBING: 3,
        Trait.COOPERATION: 3,
        Trait.FORAGING: 2,
        Trait.SCAVENGER: 2,
    }

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
        self.watering_hole = 0

    def update_state(self, player_state):
        """ Updates the player's state given its PlayerState
        :param player_state: PlayerState as defined in ExternalPlayer
        """
        species, bag, cards = player_state
        self.bag = bag
        self.species = [Species.deserialize(s) for s in species]
        self.cards = [TraitCard.deserialize(c) for c in cards]

    def start(self, watering_hole, player_state):
        """ Called at the beginning of a turn, informs the player about their current state.
        :param watering_hole: number of tokens available at the watering hole
        :param player_state: PlayerState representing the current state of the player
        """
        self.update_state(player_state)
        self.watering_hole = watering_hole

    def weight(self, value):
        """
        Determines the weight of a trait card.
        :param value: The trait card
        :return: The weight of this trait card
        """
        v_trait = value
        val = self.TRAIT_ORDERING[v_trait] if v_trait in self.TRAIT_ORDERING else 1
        return val

    def choose(self, preceding, following):
        """ Determines the actions to perform with the player's cards, i.e. the card to discard, the cards to
          exchange for body or population growth, etc.
        :param preceding: Players representing the state of players that precede this player in this turn
        :param following: Players representing the state of players that follow this player in this turn
        :return: Actions representing the player's chosen actions with their cards
        """
        # preceding = [self.deserialize(p) for p in preceding]
        # following = [self.deserialize(p) for p in following]

        # this strategy tries to produce species that are aggressive

        sorted_cards_with_indices = sorted(enumerate(self.cards),
                                           key=lambda index_card: (self.weight(index_card[1].trait),
                                                                   index_card[1].value),
                                           reverse=True)

        # the card with lowest value goes toward watering hole
        discard, _ = sorted_cards_with_indices.pop(len(sorted_cards_with_indices) - 1)
        indices_in_order = [index for index, card in sorted_cards_with_indices]

        gp, gb, bt, rt = [], [], [], []

        def count_cards_by_weight(lst, wt=1):
            elems = [elem for elem in lst if self.weight(elem[1].trait) == wt]
            idxs = [idx for idx, t in elems]
            return sorted(idxs, reverse=True)

        def count_cards_by_trait(lst, trait):
            elems = [elem for elem in lst if elem[1].trait == trait]
            idxs = [idx for idx, t in elems]
            return sorted(idxs, reverse=True)

        non_aggressive_cards = count_cards_by_weight(sorted_cards_with_indices, 1)
        carnivore_cards = count_cards_by_trait(sorted_cards_with_indices, Trait.CARNIVORE)

        pack_hunting_cards = count_cards_by_trait(sorted_cards_with_indices, Trait.PACK_HUNTING)
        ambush_cards = count_cards_by_trait(sorted_cards_with_indices, Trait.AMBUSH)
        climbing_cards = count_cards_by_trait(sorted_cards_with_indices, Trait.CLIMBING)
        cooperation_cards = count_cards_by_trait(sorted_cards_with_indices, Trait.COOPERATION)
        foraging_cards = count_cards_by_trait(sorted_cards_with_indices, Trait.FORAGING)
        scavenger_cards = count_cards_by_trait(sorted_cards_with_indices, Trait.SCAVENGER)

        species_to_make = min(len(non_aggressive_cards), len(carnivore_cards))

        def get_most_aggressive_cards():
            cards = []
            pack_hunting, ambush, climbing, cooperation, foraging, scavenger = False, False, False, False, False, False

            while len(cards) < 2:
                if len(pack_hunting_cards) > 0 and not pack_hunting and len(cards) < 2:
                    card = pack_hunting_cards.pop(0)
                    cards.append(card)
                    pack_hunting = True
                if len(ambush_cards) > 0 and not ambush and len(cards) < 2:
                    card = ambush_cards.pop(0)
                    cards.append(card)
                    ambush = True
                if len(climbing_cards) > 0 and not climbing and len(cards) < 2:
                    card = climbing_cards.pop(0)
                    cards.append(card)
                    climbing = True
                if len(cooperation_cards) > 0 and not cooperation and len(cards) < 2:
                    card = cooperation_cards.pop(0)
                    cards.append(card)
                    cooperation = True
                if len(foraging_cards) > 0 and not foraging and len(cards) < 2:
                    card = foraging_cards.pop(0)
                    cards.append(card)
                    foraging = True
                if len(scavenger_cards) > 0 and not scavenger and len(cards) < 2:
                    card = scavenger_cards.pop(0)
                    cards.append(card)
                    scavenger = True
                if len(cards) < 2:
                    # we have gone through all possibilities and not achieved 2
                    break

            return cards

        used_card_indices = []
        if species_to_make > 0:
            for i in range(species_to_make):
                discard_card = non_aggressive_cards.pop(0)  # smallest index value at end
                most_aggressive_cards = get_most_aggressive_cards()
                cards_to_add = sorted(most_aggressive_cards, reverse=True)  # smallest index value at end
                carnivore_card = carnivore_cards.pop(0)

                bt_choice = [discard_card, carnivore_card]
                bt_choice.extend(cards_to_add)
                used_card_indices.extend(bt_choice)
                bt.append(bt_choice)

        used_card_indices_sorted = sorted(used_card_indices, reverse=True)

        for idx in used_card_indices_sorted:
            indices_in_order.remove(idx)

        # If there are cards left:
        # try to increase population for each species, starting with new species, then existing species by population
        num_new_pop_reqs = min(len(indices_in_order), species_to_make)
        if num_new_pop_reqs > 0:
            for i in range(num_new_pop_reqs):
                new_species_index = len(self.species) + i
                gp.append([new_species_index, indices_in_order.pop(0)])

        num_existing_pop_reqs = min(len(indices_in_order), len(self.species))
        if num_existing_pop_reqs > 0:
            sorted_existing_species = sorted(enumerate(self.species), key=lambda s: s[1].population)
            for i in range(num_existing_pop_reqs):
                sp = sorted_existing_species.pop(0)
                if sp[1].can_grow_population(1):
                    gp.append([sp[0], indices_in_order.pop(0)])

        # If there are still cards left:
        # try to increase body for each species, starting with new species, then existing species sorted by body
        num_new_body_reqs = min(len(indices_in_order), species_to_make)
        if num_new_body_reqs > 0:
            for i in range(num_new_body_reqs):
                new_species_index = len(self.species) + i
                gb.append([new_species_index, indices_in_order.pop(0)])

        num_existing_body_reqs = min(len(indices_in_order), len(self.species))
        if num_existing_body_reqs > 0:
            sorted_existing_species = sorted(enumerate(self.species), key=lambda s: s[1].body)
            for i in range(num_existing_body_reqs):
                sp = sorted_existing_species.pop(0)
                if sp[1].can_grow_body(1):
                    gb.append([sp[0], indices_in_order.pop(0)])

        # no rt

        res = [discard, gp, gb, bt, rt]
        return res

    def feed_next(self, player_state, players, watering_hole):
        """ Determines a feeding outcome based on the given data.
        :param player_state: PlayerState representing the player's current state
        :param players: Players representing each player's species in the game order of the players
        :param watering_hole: integer representing the number of food tokens left in the watering hole
        :returns: Feeding representing the player's feeding choice
        """
        self.update_state(player_state)
        self.watering_hole = watering_hole

        players = [self.deserialize(p) for p in players]

        def trait_value(traits):
            # most valuable traits has largest
            s = -sum(self.weight(t) for t in traits)
            return s

        def species_value(species):
            return 1 + len(species.traits)

        def player_score(player):
            return sum(species_value(s) for s in player.species)

        # choose the most valuable species to attack
        carnivore_feedings = self.get_possible_carnivore_feedings(players)

        if carnivore_feedings:
            def cfeeding_score(player_index, species_index):
                player = players[player_index]
                species = player.species[species_index]
                return player_score(player), trait_value(species.traits), species_value(species)

            carnivore_feedings.sort(key=lambda f: cfeeding_score(f.player_index, f.defender_index), reverse=True)
            return carnivore_feedings[0].serialize()

        # choose the most valuable vegetarian to feed
        vegetarian_feedings = self.get_possible_vegetarian_feedings()
        if vegetarian_feedings:
            def vfeeding_score(species_index):
                species = self.species[species_index]
                return trait_value(species.traits), species_value(species)

            vegetarian_feedings.sort(key=lambda f: vfeeding_score(f.species_index), reverse=True)
            return vegetarian_feedings[0].serialize()

        # feed the species that can store the most fat tissue
        fat_feedings = self.get_possible_fat_tissue_feedings(watering_hole)
        if fat_feedings:
            fat_feedings.sort(key=lambda f: f.food_tokens, reverse=True)
            return fat_feedings[0].serialize()

        return NoFeeding().serialize()
