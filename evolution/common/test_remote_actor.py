import json
import socket

from unittest import TestCase
from unittest.mock import MagicMock

from .remote_actor import RemoteActor


class RemoteActorTestCase(TestCase):

    def test_receive(self):

        values = [
            [],
            None,
            True,
            False,
            "test",
            12346789,
            0.00000001,
            {},
        ]

        sock = MagicMock()
        sock.gettimeout.return_value = 5
        ra = RemoteActor(sock)

        def raiser(data):
            yield data
            raise socket.timeout()

        for value in values:
            data = json.dumps(value).encode("utf-8")

            sock.recv.side_effect = raiser(data)
            self.assertEqual(ra.receive(), value)

    def test_receive_iterator(self):

        values = [
            [],
            None,
            True,
            False,
            "test",
            12346789,
            0.00000001,
            {},
        ]

        data = " ".join(json.dumps(value) for value in values)
        data = data.encode("utf-8")

        sock = MagicMock()
        sock.gettimeout.return_value = 5
        ra = RemoteActor(sock)

        def raiser(data):
            yield data
            raise socket.timeout()

        sock.recv.side_effect = raiser(data)
        received = []
        try:
            for v in ra.receive_iterator():
                received.append(v)
        except socket.timeout:
            pass

        self.assertEqual(len(values), len(received))
        for expected, actual in zip(values, received):
            self.assertEqual(expected, actual)
