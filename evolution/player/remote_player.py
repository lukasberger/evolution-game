"""
    Implements the remote proxy for a networked player.

"""


from ..common.remote_actor import RemoteActor
from .external_player import ExternalPlayer


class RemotePlayer(ExternalPlayer, RemoteActor):

    def start(self, watering_hole, player_state):
        species, bag, cards = player_state
        data = [watering_hole, bag, species, cards]
        self.send(data)

    def choose(self, preceding, following):
        self.send([preceding, following])
        return self.receive()

    def feed_next(self, player_state, players, watering_hole):
        species, bag, cards = player_state
        data = [bag, species, cards, watering_hole, players]
        self.send(data)
        return self.receive()
