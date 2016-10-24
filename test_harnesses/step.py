import os
import sys
import json

PROJECT_ROOT = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")
sys.path.insert(0, PROJECT_ROOT)

from evolution.dealer.dealer import Dealer
from evolution.data_definitions import DataDefinitions


"""
    A Configuration is [LOP+, Natural, LOC].

    where LOP+ is a list of Player+, defined in Player
          Natural is a natural number as defined in DataDefinitions
          LOC is a list of trait cards, as defined in DataDefintions
"""


def feed1(configuration):
    """ Initializes a dealer from the given configuration, performs one step of a feeding
    :param configuration: initial dealer configuration
    :return: configuration after the feeding
    """
    assert DataDefinitions.dealer(configuration)
    dealer = Dealer.deserialize(configuration)
    dealer.feed1()
    return dealer.serialize()


if __name__ == "__main__":
    configuration = json.load(sys.stdin)
    configuration_after = feed1(configuration)
    print(json.dumps(configuration_after))
