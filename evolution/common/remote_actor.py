"""
    Implements a mixin for remote communication.
"""

import json
import signal


class RemoteActor:

    ENCODING = "utf-8"
    TIMEOUT = 5

    def __init__(self, socket):
        """ Creates a new remote actor able to send and receive from the given socket
        :param socket: socket connection
        """
        self.socket = socket

    def send(self, data):
        """ Sends the given JSON object to the socket
        :param data: JSON object
        """
        encoded = json.dumps(data).encode(self.ENCODING)
        print("sent", data)
        self.socket.send(encoded)

    def receive(self):
        """ Continuously receives bytes until a JSON object can be deserialized, at which point
          the deserialized object is returned. It is up to the caller to restrict the execution time.
        :return: deserialized JSON object
        """
        data = bytes()
        while True:
            data += self.socket.recv(1)
            try:
                decoded = data.decode(self.ENCODING).strip()
                decoded = json.loads(decoded)
                print("received", decoded)
                return decoded
            except (ValueError, UnicodeDecodeError):
                continue

    def receive_restricted(self, timeout=TIMEOUT):
        """ Same as receive, but with execution time limited to timeout
        :param timeout: maximum number of seconds to receive for
        :return: received data
        """
        def timeout_handler(signum, frame):
            raise TimeoutError()

        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)
        message = self.receive()
        signal.alarm(0)
        return message

    def receive_iterator(self):
        """ Continuously receives data and deserializes JSON objects as they come in """
        while True:
            yield self.receive()
