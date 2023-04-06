"""Docstring."""


class HomeworkError(Exception):
    """Docstring."""

    def __eq__(self, __value: object) -> bool:
        """Docstring."""
        return type(self) is type(__value) and self.args == __value.args


class RequestError(HomeworkError):
    """Docstring."""


class ParseResponseError(HomeworkError):
    """Docstring."""
