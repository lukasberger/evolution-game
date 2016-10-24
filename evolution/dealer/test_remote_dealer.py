from unittest import TestCase
from unittest.mock import MagicMock

# from ..player.dummy_player import DummyPlayer
from .remote_dealer import RemoteDealer


class RemoteDealerTestCase(TestCase):

    def setUp(self):
        self.player = MagicMock()
        self.sock = MagicMock()

    def test_main(self):

        rd = RemoteDealer(self.sock, self.player)

        messages = [
            ('start', [10, 0, [[['food', 0], ['body', 0], ['population', 1], ['traits', []]]],
                       [[-3, 'ambush'], [-2, 'ambush'], [-1, 'ambush']]]),
            ('choose', [[],
                        [[[['food', 0], ['body', 0], ['population', 1], ['traits', []]]],
                         [[['food', 0], ['body', 0], ['population', 1], ['traits', []]]]]]),
            ('feed_next',  [0, [[['food', 0], ['body', 0], ['population', 1], ['traits', []]],
                                [['food', 0], ['body', 0], ['population', 1], ['traits', ['ambush']]]],
                            [], 3,
                            [[[['food', 0], ['body', 0], ['population', 1], ['traits', []]],
                              [['food', 0], ['body', 0], ['population', 1], ['traits', ['ambush']]]],
                             [[['food', 0], ['body', 0], ['population', 1], ['traits', []]],
                              [['food', 0], ['body', 0], ['population', 1], ['traits', ['burrowing']]]]]]),
        ]

        for method_name, message in messages:
            setattr(rd, method_name, MagicMock())
            method = getattr(rd, method_name)
            self.assertFalse(method.called, "{} called".format(method_name))
            rd.process_message(message)
            self.assertTrue(method.called, "{} not called".format(method_name))

    def test_start(self):

        player = MagicMock()
        rd = RemoteDealer(self.sock, player)

        bag = 0
        species = [[['food', 0], ['body', 0], ['population', 1], ['traits', []]]]
        cards = [[-3, 'ambush'], [-2, 'ambush'], [-1, 'ambush']]
        watering_hole = 10

        message = [watering_hole, bag, species, cards]
        player_state = [species, bag, cards]

        self.assertFalse(player.start.called)
        rd.start(message)
        player.start.assert_called_once_with(watering_hole, player_state)

    def test_choose(self):

        player = MagicMock()
        rd = RemoteDealer(self.sock, player)

        preceding = []
        following = [[[['food', 0], ['body', 0], ['population', 1], ['traits', []]]],
                     [[['food', 0], ['body', 0], ['population', 1], ['traits', []]]]]
        message = [preceding, following]

        player.choose.return_value = ""
        self.assertFalse(player.choose.called)
        rd.choose(message)
        player.choose.assert_called_once_with(preceding, following)

    def test_feed_next(self):

        player = MagicMock()
        rd = RemoteDealer(self.sock, player)

        bag = 0
        species = [[['food', 0], ['body', 0], ['population', 1], ['traits', []]],
                   [['food', 0], ['body', 0], ['population', 1], ['traits', ['ambush']]]]
        cards = []
        watering_hole = 3
        players = [[[['food', 0], ['body', 0], ['population', 1], ['traits', []]],
                    [['food', 0], ['body', 0], ['population', 1], ['traits', ['ambush']]]],
                   [[['food', 0], ['body', 0], ['population', 1], ['traits', []]],
                    [['food', 0], ['body', 0], ['population', 1], ['traits', ['burrowing']]]]]

        message = [bag, species, cards, watering_hole, players]
        player_state = [species, bag, cards]

        player.feed_next.return_value = ""
        self.assertFalse(player.feed_next.called)
        rd.feed_next(message)
        player.feed_next.assert_called_once_with(player_state, players, watering_hole)
