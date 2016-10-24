"""
    Implements an Evolution client with the silly player strategy.
    The client connects to an evolution server on the given host and port and listens for, processes and
    responds to messages.
"""

import socket

from argparse import ArgumentParser

from evolution.dealer.remote_dealer import RemoteDealer
from evolution.player.strategy_player import StrategyPlayer

DEFAULT_HOST = "antarctica.ccs.neu.edu"
DEFAULT_PORT = 45678

HELLO_MESSAGE = "xman"


def main(host, port):
    """ Connects to an Evolution server on the given host/port, performs the sign up sequence and
      then continuously listens for messages from the server and responds accordingly.
    :param host: evolution host
    :param port: evolution port
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))

    player = StrategyPlayer(1)
    dealer = RemoteDealer(s, player)

    print("Sending hello message: \"{}\"".format(HELLO_MESSAGE))
    dealer.send(HELLO_MESSAGE)
    print("Response received: {}".format(dealer.receive()))

    dealer.main()


def parse_args():
    """ Parses command-line arguments. """
    parser = ArgumentParser(description="Launches a new Evolution client, which tries to connect to the given server")
    parser.add_argument("-i", "--host", help="server host to connect to", default=DEFAULT_HOST)
    parser.add_argument("-p", "--port", help="server port to connect to", type=int, default=DEFAULT_PORT)

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    main(args.host, args.port)
