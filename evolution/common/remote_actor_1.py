"""
    Implements a mixin for remote communication.
"""

import json
import socket

decoder = json.JSONDecoder()


class RemoteActor:

    ENCODING = "utf-8"

    def __init__(self, socket):
        """ Creates a new remote actor able to send and receive from the given socket
        :param socket: socket connection
        """
        self.socket = socket
        self.timeout = socket.gettimeout()
        self.buffer = ""

    def send(self, data):
        """ Sends the given JSON object to the socket
        :param data: JSON object
        """
        encoded = json.dumps(data).encode(self.ENCODING)
        self.socket.send(encoded)

    def decode(self, final=False):
        decoded, end = decoder.raw_decode(self.buffer)
        # was able to decode a json object and there is data left over
        if end < (len(self.buffer) - 1) and not isinstance(decoded, float):
            self.buffer = self.buffer[end:].lstrip()
            return decoded
        # no data left over
        elif final:
            self.buffer = ""
            return decoded
        else:
            raise ValueError("number could have more bytes")

    def receive(self):
        """ Continuously receives bytes until a JSON object can be deserialized, at which point
          the deserialized object is returned. It is up to the caller to restrict the execution time.
        :return: deserialized JSON object
        """
        while True:
            try:
                data = self.socket.recv(1)
                decoded = data.decode(self.ENCODING)
                self.buffer += decoded
                return self.decode()
            except (ValueError, UnicodeDecodeError):
                continue
            except socket.timeout:
                self.ontimeout()

    def receive_iterator(self):
        """ Continuously receives data and deserializes JSON objects as they come in """
        while True:

            data = self.receive()
            print(data, self.buffer)
            yield data

    def ontimeout(self):
        decoded = self.decode(final=True)
        if decoded:
            return decoded
        else:
            raise socket.timeout()
