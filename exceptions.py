"""Docstring."""

from requests import RequestException


class HomeworkError(Exception):
    """Docstring."""

    def need_notify(self) -> bool:
        """Docstring."""
        return False


class RequestError(HomeworkError):
    """Docstring."""

    def need_notify(self) -> bool:
        """Docstring."""
        return isinstance(self.__cause__, RequestException)


class ParseResponseError(HomeworkError):
    """Docstring."""
