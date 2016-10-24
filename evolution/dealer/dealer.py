"""

    This file implements the Dealer for the Evolution game.

    In the game world, a Dealer configuration is expressed by a Configuration.

    A Configuration is [LOP+, Natural, LOC].

    where LOP+ is a list of Player+, defined in Player
          Natural is a natural number as defined in DataDefinitions
          LOC is a list of trait cards, as defined in DataDefinitions

"""

from ..data_definitions import DataDefinitions

from ..player.player import Player

from ..common.trait import HORNS_DAMAGE
from ..common.trait_card import TraitCard


class Dealer:
    """ Contains a representation of the state of the game. """

    # watering hole minimum
    WATERING_HOLE_MINIMUM = 0
    # how much population a defending species loses when successfully attacked
    CARNIVORE_ATTACK_POPULATION_DECREASE = 1
    # number of cards given to the owner of a species that goes extinct
    EXTINCT_SPECIES_PAYOUT = 2
    # number of cards to give to each player at the beginning of each turn
    CARDS_PER_TURN = 3
    # number of cards to give to each player for each species at the beginning of a turn
    CARDS_PER_SPECIES = 1
    # index of the starting player
    STARTING_PLAYER_IDX = 0

    # Configuration constants
    CONFIGURATION_PLAYERS_MIN = 3
    CONFIGURATION_PLAYERS_MAX = 8

    # Display method constants
    DISPLAY_KEY_WATERING_HOLE = "watering-hole"
    DISPLAY_KEY_PLAYERS = "players"
    DISPLAY_KEY_DECK = "deck"

    def __init__(self, players=None, watering_hole=None, deck=None):
        """ Creates a new Dealer instance
        :param players: list of players in the game in order of their turn
        :param watering_hole: number of tokens in the watering hole
        :param deck: list of TraitCards in the deck
        :return: an instance of dealer
        """
        self.watering_hole = watering_hole if watering_hole is not None else self.WATERING_HOLE_MINIMUM
        self.players = players.copy() if players is not None else []
        self.deck = deck.copy() if deck is not None else []

        # players who can still feed, set and used during step4
        self.active_players = self.players.copy()

    def add_external_players(self, players):
        """ Adds the given external players to the game. Any existing external players are replaced.
          Effect: replaces any existing players with internal players linked to the given players
        :param players: list of external players
        :return: list of ids assigned to each player, the ids correspond to each player in the given list
        """
        self.players = [Player(idx + 1, external=player) for idx, player in enumerate(players)]
        return [p.idx for p in self.players]

    def run_game(self):
        """ Simulates an entire Evolution game
          * for determinism the dealer deals cards in their sorted order, smallest first
          * the turns repeat as long as there are enough cards to deal out to all player
        """
        self.deck = sorted(DataDefinitions.deck())

        def num_cards_to_deal():
            return sum(self.num_cards_to_deal(player) for player in self.players)

        while num_cards_to_deal() <= len(self.deck):
            self.take_turn()
            # if there are no more players stop the main loop
            if not self.players:
                break
            # the order of players is determined in round-robin fashion
            self.players = self.players[1:] + self.players[:1]

    @classmethod
    def num_cards_to_deal(cls, player):
        """ Returns the number of cards to deal for the given player
        :param player: player to deal the cards to
        :return: number of cards to deal to the given player
        """
        # each player has at least one species that it's given at the beginning of a turn
        num_species = max(1, len(player.species))
        return cls.CARDS_PER_TURN + cls.CARDS_PER_SPECIES * num_species

    def take_turn(self):
        """ Simulates one turn in a game of Evolution, each turn consists of the following steps:
          * step1: dealer hands a species board to each player that doesn't have one
                   and gives the player a specified number of cards + 1 per species
          * step2/3: choose a card to discard along with cards to use for other purposes
          * step4: apply the chosen actions and feed
        """
        self.step1()
        action_list = self.step2_3()
        self.step4(action_list)
        self.end_turn()

    def step1(self):
        """ Performs step1 of a turn. Gives each player who doesn't have one a species board
          and then a specific number of cards along with an additional one for each species.
          Effect: if any issues occurred when calling the external player, the player is removed from the game
        """
        def start_step(player):
            has_any_species = len(player.species) > 0
            new_species = not has_any_species
            cards_to_give = self.deal_cards(self.num_cards_to_deal(player))
            return player.start(self.watering_hole, new_species, cards_to_give)

        self.apply_to_all_players(start_step)

    def deal_cards(self, n):
        """ Remove and return the n topmost cards from the deck or less if less are available.
        :param n: number of cards to remove
        :return: up to n topmost cards from the deck
        """
        cards_to_remove = min(n, len(self.deck))
        return [self.deck.pop(0) for _ in range(cards_to_remove)]

    def apply_to_all_players(self, function):
        """ Applies the given function to all players in the game, in order. If there is an issue with the
          external player, the player is kicked out of the game.

          Effect: modifies self.players, removing problematic players if necessary
          Invariant: len(response) == len(self.players)

        :param function: function that expects a player object to be executed on each player
        :return: result of the executions of the given function on each player, results from removed player are
                 omitted from the list
        """
        answers = []
        bad_players = []
        for player_idx, player in enumerate(self.players):
            response = function(player)
            valid, content = self.handle_player_response(response)
            # remove the player if the response was invalid
            if valid:
                answers.append(content)
            else:
                bad_players.append(player_idx)

        bad_players.reverse()
        for bad_player_idx in bad_players:
            self.players.pop(bad_player_idx)

        return answers

    def handle_player_response(self, response):
        """ Handles a player response. If the response is valid, returns the content.
          Effect: removes the player at the given index from the game if the response in invalid.
        :param response: PlayerResponse
        :return: (valid, content) where valid is a boolean and content is the content or None
        """
        if response.valid():
            return True, response.content()
        else:
            return False, None

    def step2_3(self):
        """ Performs steps 2 and 3 of a turn.
            * asks each player for a card to discard
            * asks each player to choose which actions they wish to perform
          Effect: if any issues occurred when calling the external player or if the response is invalid,
                  the player is removed from the game
        :return: list of Actions objects representing the chosen actions of each player
        """
        def choose_step(player):
            return player.choose(self.players)

        return self.apply_to_all_players(choose_step)

    def step4(self, action_list):
        """ Performs step 4 of a turn:
          * the dealer turns over the food cards placed at the watering hole and executes the actions that the
            players have chosen in step 3
          * activates the auto-feeding trait cards that players have associated with their species;
            the food is taken from the watering hole.
        :param action_list: list of Actions, the action at each position in the list corresponds to the player at the
                            same position the the list of players; all actions must be valid
        """
        for player_idx, actions in enumerate(action_list):
            self.apply_actions(player_idx, actions)

        self.auto_traits()
        self.feeding_step()

    def apply_actions(self, player_index, actions):
        """ Applies the given Actions object for the player at the given index
          Effect: modifies the watering hole based on the player's discard card
        :param player_index: index of the player to apply the actions for
        :param actions: Actions object storing the player's requested actions
        """
        player = self.players[player_index]
        discard_value = actions.apply(player)
        self.update_watering_hole(discard_value)

    def auto_traits(self):
        """ Effect: feeds all players' species in order, based on their auto-feeding traits, updates the watering
          hole to reflect consumed tokens.
        """
        for player in self.players:
            self.watering_hole -= player.auto_traits(self.watering_hole)

    def feeding_step(self):
        """ Runs the feeding step until all players' species are fed or there is no more food in the watering hole
        """
        self.reset_active_players()

        while self.watering_hole > self.WATERING_HOLE_MINIMUM and self.active_players:
            self.feed1()

    def feed1(self):
        """ Perform one step of the feeding. The watering hole cannot be empty.
            * asks the player for the next feeding, determined automatically if possible or by choice
            * applies the feeding
          Effect: rotates the player order at the end
        """
        current_player = self.get_current_player()
        current_player_index = self.players.index(current_player)
        feeding_outcome_response = current_player.feeding_choice(self.player_queue_all[1:], self.watering_hole)

        valid_response, feeding_outcome = self.handle_player_response(feeding_outcome_response)

        # remove player from game for invalid responses
        if not valid_response or not feeding_outcome.validate(self):
            self.players.pop(current_player_index)
            remove_player_from_active = True
        else:
            remove_player_from_active = feeding_outcome.apply(self)

        if remove_player_from_active:
            self.remove_current_player_from_active()
        else:
            self.rotate_active_players()

    def end_turn(self):
        """ Performs the end of turn action for all players, awarding each player with the
          appropriate number of cards for each extinct species.
        """
        for player in self.players:
            extinct_species = player.end_turn()
            for _ in range(extinct_species):
                self.species_extinct(player)

    def update_watering_hole(self, delta):
        """ Updates the watering hole tokens by the given number, the number of tokens will never go below
          the WATERING_HOLE_MINIMUM
        :param delta: number by which to update the watering hole
        """
        self.watering_hole += delta
        self.watering_hole = max(self.watering_hole, self.WATERING_HOLE_MINIMUM)

    def get_current_player(self):
        """ Returns the player whose turn it is to feed its species
        :return: player whose turn it is to feed its species
        """
        return self.active_players[0]

    @property
    def player_queue_all(self):
        """ Represents the list of all players in their playing order, starting with the current player. """
        player_index = self.players.index(self.get_current_player())
        return self.players[player_index:] + self.players[:player_index]

    def feed_species(self, player, species_index):
        """ Feeds the species at the given index of the given player.
          Effect: subtracts the number of consumed food tokens by each player from the watering hole
        :param player: player who owns the species
        :param species_index: index of the species to feed
        """
        food_taken = player.feed_species(species_index, self.watering_hole)
        self.watering_hole -= food_taken

    def feed_species_fat_tissue(self, player, species_index, food_tokens):
        """ Stores the given number of food tokens on the species at the given index of the given player.
          Effect: subtracts the number of consumed food tokens by each player from the watering hole
        :param player: player who owns the species
        :param species_index: index of the species to store fat tissue for
        :param food_tokens: number of food tokens to store
        """
        player.store_fat_tissue(species_index, food_tokens)
        self.watering_hole -= food_tokens

    def carnivore_feeding(self, species_index, defending_player_index, defending_species_index):
        """ Performs a carnivore feeding for the carnivore at the given species_index on the
          species located at the defender_index owned by the player at the given player_index.
        :param species_index: index of the attacker in the list of species of the current player
        :param defending_player_index: index of the player in the list of players, starting from the player
                                       immediately following the current player; this list contains the current
                                       player at the last position
        :param defending_species_index: index of the defending species in the list of species of the defending player
        """
        current_player = self.get_current_player()
        # the list of possible target players as seen by the current player
        defender_list = self.player_queue_all[1:] + [current_player]
        defending_player = defender_list[defending_player_index]

        _, defender_horns = self.hurt_species(defending_player, defending_species_index,
                                              self.CARNIVORE_ATTACK_POPULATION_DECREASE)

        if defender_horns:
            attacker_died, _ = self.hurt_species(current_player, species_index, HORNS_DAMAGE)
        else:
            attacker_died = False

        if not attacker_died:
            self.feed_species(current_player, species_index)
            self.scavenge()

    def scavenge(self):
        """ Informs all players in order that a carnivore ate.
          Effect: subtracts the number of consumed food tokens by each player from the watering hole
        """
        for player in self.player_queue_all:
            food_taken = player.scavenge(self.watering_hole)
            self.watering_hole -= food_taken

    def hurt_species(self, player, species_index, damage):
        """ Kills off `damage' population of the species at the given index belonging to the given player.
          If the species goes extinct, performs the appropriate action for an extinct species.
        :param player: player who owns the species
        :param species_index: index of the species to hurt
        :param damage: damage to inflict on the species population
        :return: (did species go extinct, does the species have horns) tuple
        """
        species_extinct, horns = player.hurt_species(species_index, damage)
        if species_extinct:
            self.species_extinct(player)

        return species_extinct, horns

    def species_extinct(self, player):
        """ Triggered when a species owned by the given player goes extinct.
          Effect: hand the player the appropriate amount of cards
        :param player: owner of the species
        """
        player.add_cards(self.deal_cards(self.EXTINCT_SPECIES_PAYOUT))

    def ranking(self):
        """ Computes the player ranking based on the number of tokens in each player's food bag; the player
          with the most tokens is first.
        :return: generator yielding (idx, bag tokens) for each player in order of the ranking
        """
        players_ranked = sorted(self.players, key=lambda p: p.score(), reverse=True)
        for player in players_ranked:
            yield player.idx, player.score()

    def serialize(self):
        """ Returns the dealer's Configuration
        :return: the dealer's Configuration
        """
        players = [player.serialize() for player in self.players]
        deck = [card.serialize() for card in self.deck]
        return [players, self.watering_hole, deck]

    @classmethod
    def deserialize(cls, data):
        """ Creates a Dealer object from the given configuration. Constraints:
            * the list of players must contain at least 3 and at most 8 players
            * the list of all cards must make a subset of all cards in evolution
        :param data: a JSON Dealer configuration
        :return: Dealer
        """
        lop, watering_hole, loc = data

        players = [Player.deserialize(player) for player in lop]
        deck = [TraitCard.deserialize(card) for card in loc]

        return cls(players, watering_hole, deck)

    def display(self):
        """ Returns a data representation of the dealer that can be used in a view
        :return: data representation of a dealer to be used in a view
        """
        return {
            self.DISPLAY_KEY_WATERING_HOLE: self.watering_hole,
            self.DISPLAY_KEY_PLAYERS: [p.display() for p in self.players],
            self.DISPLAY_KEY_DECK: [tc.display() for tc in self.deck],
        }

    def reset_active_players(self):
        """ Resets the active players based on current order of players in the game.
          Effect: modifies self.active_players
        """
        self.active_players = self.players.copy()

    def rotate_active_players(self):
        """ Rotates the list of active players, putting the first player at the end
          Effect: modifies self.active_players
        """
        self.active_players = self.active_players[1:] + self.active_players[:1]

    def remove_current_player_from_active(self):
        """ Removes the first player from the list of active players
          Effect: modifies self.active_players
        """
        self.active_players.pop(0)
