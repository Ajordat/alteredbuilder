from rest_framework import status
from api.exceptions import AlteredBuilderException


# Custom exceptions inheriting from the base exception defined on the API app


class DeckException(AlteredBuilderException):
    pass


class MalformedDeckException(DeckException):
    def __init__(self, detail: str):
        super().__init__(detail, status.HTTP_400_BAD_REQUEST)
