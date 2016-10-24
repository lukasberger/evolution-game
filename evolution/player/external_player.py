"""

    Describes the interface for an external player in the Evolution game.

    Players is a [LOS, ...] where each LOS corresponds to an individual player
    PlayerState [LOS, Natural, LOC], representing the players species, bag, and cards respectively

"""


class ExternalPlayer:

    def start(self, watering_hole, player_state):
        """ Called at the beginning of a turn, informs the player about their current state.
        :param watering_hole: number of tokens available at the watering hole
        :param player_state: PlayerState representing the current state of the player
        """
        raise NotImplementedError("An external player must implement this method.")

    def choose(self, preceding, following):
        """ Determines the actions to perform with the player's cards, i.e. the card to discard, the cards to
          exchange for body or population growth, etc.
        :param preceding: Players representing the state of players that precede this player in this turn
        :param following: Players representing the state of players that follow this player in this turn
        :return: Actions representing the player's chosen actions with their cards
        """
        raise NotImplementedError("An external player must implement this method.")

    def feed_next(self, player_state, players, watering_hole):
        """ Determines a feeding outcome based on the given data.
        :param player_state: PlayerState representing the player's current state
        :param players: Players representing each player's species in the game order of the players
        :param watering_hole: integer representing the number of food tokens left in the watering hole
        :returns: Feeding representing the player's feeding choice
        """
        raise NotImplementedError("An external player must implement this method.")
