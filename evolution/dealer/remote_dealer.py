"""
    Implements the remote proxy for a networked dealer.

"""


from ..common.remote_actor import RemoteActor


class RemoteDealer(RemoteActor):

    START_MESSAGE_LEN = 4
    CHOOSE_MESSAGE_LEN = 2
    FEED_NEXT_MESSAGE_LEN = 5

    def __init__(self, socket, player):
        """ Creates a new proxy for a remote dealer
        :param socket: socket connection
        :param player: ExternalPlayer
        """
        super().__init__(socket)
        self.player = player

    def main(self):
        """ Starts the main loop for the remote dealer. The dealer listens for incoming messages from the
          server and performs the appropriate action on each received message. """
        for message in self.receive_iterator():
            self.process_message(message)

    def process_message(self, message):
        """ Processes the given message. A message is one of:
          * PlayerState, for start
          * [LOB, LOB], for choose
          * State, for feed_next
        :param message: message to process
        """
        if len(message) == self.START_MESSAGE_LEN:
            self.start(message)
        elif len(message) == self.CHOOSE_MESSAGE_LEN:
            self.choose(message)
        elif len(message) == self.FEED_NEXT_MESSAGE_LEN:
            self.feed_next(message)

    def start(self, data):
        """ Processes a start message of the format PlayerState
        :param data: PlayerState
        """
        watering_hole, bag, species, cards = data
        player_state = [species, bag, cards]
        self.player.start(watering_hole, player_state)

    def choose(self, data):
        """ Processes a choose message of the format [LOB, LOB]. Sends the player's response back to the server.
        :param data: [LOB, LOB]
        """
        preceding, following = data
        response = self.player.choose(preceding, following)
        self.send(response)

    def feed_next(self, data):
        """ Processes a feed_next message of the format State and sends the player's response back to the server.
        :param data: State
        """
        bag, species, cards, watering_hole, players = data
        player_state = [species, bag, cards]
        response = self.player.feed_next(player_state, players, watering_hole)
        self.send(response)
