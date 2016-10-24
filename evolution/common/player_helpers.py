"""
    Implements a decorator to limit the execution time and handler errors
    that occur when calling an external player.
"""

import signal


def external_player_call():
    """ Decorates functions that perform calls to external players using the ExternalPlayerCall context manager.
      If there is an issue with the call, the function will return PlayerResponseInvalid, otherwise it will return
      PlayerResponseValid containing the return value.
    """
    def call_decorator(f):
        def call_wrapper(*args, **kwargs):
            try:
                value = f(*args, **kwargs)
                return PlayerResponseValid(value)
            except ExternalPlayerIssue:
                return PlayerResponseInvalid()
        return call_wrapper
    return call_decorator


class ExternalPlayerIssue(Exception):
    """ Represents an issue with the external player. An issue can be but is not limited to:
        timeouts, invalid response, exceptions, etc. """
    pass


class ExternalPlayerCall:
    """ Context manager that limits the execution time of methods called on external player and
        checks for exceptions. If a timeout occurs or an exception is raised, raises an
        ExternalPlayerIssue exception """

    TIMEOUT_THRESHOLD = 5

    @staticmethod
    def timeout_handler(signum, frame):
        raise TimeoutError()

    def __init__(self, timeout=None):
        self.timeout = timeout if timeout is not None else self.TIMEOUT_THRESHOLD

    def __enter__(self):
        signal.signal(signal.SIGALRM, self.timeout_handler)
        signal.alarm(self.timeout)

    def __exit__(self, exc_type, exc_value, exc_traceback):
        signal.alarm(0)
        # if an exception was raised
        if exc_type is not None:
            raise ExternalPlayerIssue() from exc_value


class PlayerResponse:
    """ Represents a maybe-response from a player """

    @staticmethod
    def valid():
        raise NotImplementedError("Must use a subclass.")

    def content(self):
        raise NotImplementedError("Must use a subclass.")


class PlayerResponseInvalid(PlayerResponse):
    """ Represents an invalid response from a player """

    @staticmethod
    def valid():
        return False

    def content(self):
        raise ValueError("Invalid response does not have any content.")


class PlayerResponseValid(PlayerResponse):
    """ Represents an valid response from a player """

    def __init__(self, value):
        self.value = value

    @staticmethod
    def valid():
        return True

    def content(self):
        return self.value


