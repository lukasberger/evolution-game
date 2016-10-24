"""
    Runs a complete Evolution game with the given number of Silly players.

"""

from argparse import ArgumentParser

from evolution.dealer.dealer import Dealer
from evolution.player.dummy_player import DummyPlayer


PLAYERS_MIN = 3
PLAYERS_MAX = 8


def main(n):
    """ Runs a complete Evolution game with the given number of players
    :param n: number of players in the game
    """
    assert n in range(PLAYERS_MIN, PLAYERS_MAX + 1), "invalid number of players"

    players = [DummyPlayer(idx + 1) for idx in range(0, n)]
    dealer = Dealer()
    dealer.add_external_players(players)
    dealer.run_game()

    print("Results:")
    for place, (idx, bag) in enumerate(dealer.ranking()):
        print("{} player id: {} score: {}".format(place + 1, idx, bag))


if __name__ == "__main__":

    parser = ArgumentParser(description="Simulates a complete Evolution game")
    parser.add_argument("n", type=int,
                        help="number of players in the game, in range [{}, {}]".format(PLAYERS_MIN, PLAYERS_MAX))
    args = parser.parse_args()

    main(args.n)
