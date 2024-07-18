from rest_framework import status
from api.exceptions import AlteredBuilderAPIException


# Custom exceptions inheriting from the base exception defined on the API app


class DeckException(AlteredBuilderAPIException):
    pass


class MalformedDeckException(DeckException):
    def __init__(self, detail: str):
        super().__init__(detail, status.HTTP_400_BAD_REQUEST)


class AlteredBuilderException(Exception):
    pass


class IgnoreCardType(AlteredBuilderException):
    pass
