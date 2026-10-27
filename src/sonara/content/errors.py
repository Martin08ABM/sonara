"""Controlled errors with stable codes and no private file paths."""


class ContentError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
