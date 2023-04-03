"""Docstring."""


class HomeworkError(Exception):
    """Docstring."""

    def __eq__(self, __value: object) -> bool:
        """Docstring."""
        return str(self) == str(__value)


class RequestError(HomeworkError):
    """Docstring."""


class CheckResponseError(HomeworkError):
    """Docstring."""


class ParseResponseError(HomeworkError):
    """Docstring."""


class SendMessageError(HomeworkError):
    """Docstring."""
