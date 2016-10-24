import os
import sys
import json

PROJECT_ROOT = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")
sys.path.insert(0, PROJECT_ROOT)

from evolution.player.player import Player
from evolution.player.dummy_player import DummyPlayer
from evolution.data_definitions import DataDefinitions


"""
    A Choice is [Player+, before, after]

    where Player+ is defined in Player
          before is [LOS, ..., LOS] and can be empty
          after is [LOS, ..., LOS]] and can be empty
          LOS is a list of Species+ as defined in Species

"""


def run_silly(choice):
    """ Initializes a dealer from the given configuration, performs one step of a feeding
    :param configuration: initial dealer configuration
    :param step4: step4
    :return: configuration after the feeding
    """
    assert DataDefinitions.array(choice)
    assert len(choice) == 3

    silly, before, after = choice

    def los(data):
        return DataDefinitions.array(data) and all(DataDefinitions.species(s) for s in data)

    assert DataDefinitions.player(silly)
    assert DataDefinitions.array(before) and all(los(l) for l in before)
    assert DataDefinitions.array(after) and all(los(l) for l in after)

    player = Player.deserialize(silly)
    player.external = DummyPlayer()
    player.start(new_species=None, cards=[], watering_hole=0)

    return player.external.choose(before, after)

if __name__ == "__main__":
    choice = json.load(sys.stdin)
    choice_result = run_silly(choice)
    print(json.dumps(choice_result))
