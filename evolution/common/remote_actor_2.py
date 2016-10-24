"""
    Implements a mixin for remote communication.
"""

import re
import json
import socket

whitespace_re = re.compile(r"\s+")

class RemoteActor:

    ENCODING = "utf-8"
    DECODER = json.JSONDecoder()

    def __init__(self, socket):
        """ Creates a new remote actor able to send and receive from the given socket
        :param socket: socket connection
        """
        self.socket = socket
        self.buffer = ""

    def parse(self, clear_on_partial=False):
        print(self.buffer)
        try:
            decoded, end = self.DECODER.raw_decode(self.buffer)
        except ValueError:
            print(self.buffer, "va")
            return False, False, False

        if not isinstance(decoded, bool) and (isinstance(decoded, int) or isinstance(decoded, float)) and end == len(self.buffer):
            if clear_on_partial:
                self.buffer = self.buffer[end:]
            return True, False, decoded
        else:
            print(decoded, "blah")
            self.buffer = self.buffer[end:]
            return True, True, decoded

    def send(self, data):
        """ Sends the given JSON object to the socket
        :param data: JSON object
        """
        encoded = json.dumps(data).encode(self.ENCODING)
        self.socket.send(encoded)

    def receive(self):
        """ Continuously receives bytes until a JSON object can be deserialized, at which point
          the deserialized object is returned. It is up to the caller to restrict the execution time.
        :return: deserialized JSON object
        """
        data = bytes()
        while True:
            try:
                data += self.socket.recv(1)
            except socket.timeout:
                something, complete, decoded = self.parse(True)
                print(something, complete, decoded)
                if something:
                    return decoded
                raise

            try:
                decoded = data.decode(self.ENCODING)
                self.buffer += decoded
                data = bytes()
            except UnicodeDecodeError:
                continue

            something, complete, decoded = self.parse()
            if something and complete:
                return decoded

    def receive_iterator(self):
        """ Continuously receives data and deserializes JSON objects as they come in """
        while True:
            yield self.receive()
