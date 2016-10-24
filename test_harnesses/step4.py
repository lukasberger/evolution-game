import os
import sys
import json

PROJECT_ROOT = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")
sys.path.insert(0, PROJECT_ROOT)

from evolution.dealer.dealer import Dealer
from evolution.data_definitions import DataDefinitions
from evolution.common.actions import Actions


"""
    A Configuration is [LOP+, Natural, LOC].

    where LOP+ is a list of Player+, defined in Player
          Natural is a natural number as defined in DataDefinitions
          LOC is a list of trait cards, as defined in DataDefintions


    A Step4 is [Action4, ..., Action4].


"""


def run_step4(configuration, step4):
    """ Initializes a dealer from the given configuration, performs one step of a feeding
    :param configuration: initial dealer configuration
    :param step4: step4
    :return: configuration after the feeding
    """
    assert DataDefinitions.dealer(configuration)
    dealer = Dealer.deserialize(configuration)

    assert DataDefinitions.array(step4) and all(DataDefinitions.action4(a) for a in step4)
    assert len(step4) == len(dealer.players)
    actions = [Actions.deserialize(s) for s in step4]
    dealer.step4(actions)

    return dealer.serialize()


if __name__ == "__main__":
    configuration, step4 = json.load(sys.stdin)
    configuration_after = run_step4(configuration, step4)
    print(json.dumps(configuration_after))
