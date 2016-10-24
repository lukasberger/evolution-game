import time

from unittest import TestCase
from .player_helpers import ExternalPlayerCall, ExternalPlayerIssue


class ExternalPlayerCallTestCase(TestCase):

    def test_timeout(self):
        timeout = 1
        time_to_sleep = timeout + 1
        with self.assertRaises(ExternalPlayerIssue):
            with ExternalPlayerCall(timeout):
                time.sleep(time_to_sleep)

    def test_timeout_loop(self):
        timeout = 1
        with self.assertRaises(ExternalPlayerIssue):
            with ExternalPlayerCall(timeout):
                while True:
                    pass

    def test_exception_raised(self):
        with self.assertRaises(ExternalPlayerIssue):
            with ExternalPlayerCall():
                raise ValueError("some error")

    def test_working(self):
        external_player_call = ExternalPlayerCall()

        value = None
        self.assertIsNone(value)

        with external_player_call:
            value = 1234

        self.assertEqual(value, 1234)
