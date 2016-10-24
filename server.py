"""
    Launches an Evolution server, accepts remote players and simulates a complete evolution game.

    1. listen for connections
    2. until at least 3 and at most 8 or timeout:
        1. accepts a single JSON string and sends back an ok message
        2. creates a new proxy player with a connection from above ^
    3. create a dealer and hand it the proxy players
    4. start game

"""

import socket

from time import sleep
from argparse import ArgumentParser

from evolution.dealer.dealer import Dealer
from evolution.player.remote_player import RemotePlayer

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 45679

MIN_PLAYERS = 3
MAX_PLAYERS = 8

OKAY_MESSAGE = "ok"

TIMEOUT = 5
COUNTDOWN_TIME = 5


def main(host, port):
    """ Connects to an Evolution server on the given host/port, performs the sign up sequence and
      then continuously listens for messages from the server and responds accordingly.
    :param host: evolution host
    :param port: evolution port
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, port))

    players = accept_players(s)

    print("Starting game with {} players\n".format(len(players)))
    start_game(players)


def accept_players(s):
    """ Accepts connections from remote players and returns a list of RemotePlayer objects for each successful
      connection. Returns between MIN_PLAYERS and MAX_PLAYERS players.
    :param s: socket to listen on
    :return: list of (info message, RemotePlayer)
    """
    s.listen(MAX_PLAYERS)
    players = []

    print("Waiting for players to join...")

    while len(players) < MIN_PLAYERS:
        players.append(accept_player(s))

    print("{} players joined, the game will start when {} players have joined or when "
          "no new players have joined for {} seconds".format(MIN_PLAYERS, MAX_PLAYERS, COUNTDOWN_TIME))

    # the game will start if no new players have joined for COUNTDOWN_TIME seconds
    s.settimeout(COUNTDOWN_TIME)

    try:
        while len(players) < MAX_PLAYERS:
            players.append(accept_player(s))
    except socket.timeout:
        pass

    return players


def accept_player(s):
    """ Accepts connections from the given socket and creates a new player for each connection that
      properly authenticates. If the player sends an invalid message, the process starts over.
    :param s: socket to listen on
    :return: (info message, remote player) tuple
    """
    client_socket, address = s.accept()
    client_socket.settimeout(TIMEOUT)
    remote_player = RemotePlayer(client_socket)

    try:
        hello_message = remote_player.receive()
        if isinstance(hello_message, str):
            remote_player.send(OKAY_MESSAGE)
            print("New player joined, saying: {}".format(hello_message))
            return (hello_message, remote_player)

    except socket.timeout:
        pass

    return accept_player(s)


def start_game(players):
    """ Starts the game with the given list of remote players. After the game finishes prints the results.
    :param players: list of (info message, remote player) tuples to start the game with
    """
    remote_players = [player for info_message, player in players]

    dealer = Dealer()
    player_ids = dealer.add_external_players(remote_players)
    dealer.run_game()

    id_player_map = {idx: player for idx, player in zip(player_ids, players)}

    print("Results:")
    for place, (idx, bag) in enumerate(dealer.ranking()):
        info_message, _ = id_player_map[idx]
        print("{}\tplayer id:{} info message: {}\tscore: {}".format(place + 1, idx, info_message, bag))


def parse_args():
    """ Parses command-line arguments. """
    parser = ArgumentParser(description="Launches a new Evolution server, bound to the given host and port")
    parser.add_argument("-i", "--host", help="server host to bind to", default=DEFAULT_HOST)
    parser.add_argument("-p", "--port", help="server port to bind to", type=int, default=DEFAULT_PORT)

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    main(args.host, args.port)
