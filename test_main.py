from unittest import TestCase
from unittest.mock import patch

import socket
import re

from io import StringIO
from time import sleep
from threading import Thread

from main import main as main_sequential
from client import main as main_client
from server import accept_players, start_game


class SequentialParallelTestCase(TestCase):

    def test_all_players(self):
        for n in range(3, 9):
            print("Testing {} players.".format(n))
            self.sequential_parallel(n)

    def sequential_parallel(self, players):

        host = "127.0.0.1"

        # sequential
        with patch("sys.stdout", new_callable=StringIO) as out:
            main_sequential(players)
            expected = out.getvalue()

        # parallel
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((host, 0))
        port = s.getsockname()[1]

        for i in range(players):
            t = Thread(target=main_client, args=(host, port))
            t.daemon = True
            t.start()
            sleep(0.1)

        players = accept_players(s)
        sleep(1)

        with patch("sys.stdout", new_callable=StringIO) as out:
            start_game(players)
            actual = out.getvalue()

        # the format of the response is different for sequential and parallel,
        # the parallel version also contains player message

        result_re = re.compile(r'(\d+)\s+player id:\s*(\d+).*score:\s*(\d+)')

        expected_lines = expected.strip().split("\n")
        actual_lines = actual.strip().split("\n")

        self.assertEqual(len(expected_lines), len(actual_lines))
        self.assertEqual(expected_lines.pop(0), actual_lines.pop(0))

        for expected_line, actual_line in zip(expected_lines, actual_lines):
            print("compare lines:", expected_line, actual_line)
            expected_place, expected_id, expected_points = result_re.search(expected_line).groups()
            actual_place, actual_id, actual_points = result_re.search(actual_line).groups()
            self.assertEqual(expected_place, actual_place)
            self.assertEqual(expected_id, actual_id)
            self.assertEqual(expected_points, actual_points)
