from rest_framework import status
from api.exceptions import AlteredBuilderException


class DeckException(AlteredBuilderException):
    pass


class MalformedDeckException(DeckException):
    def __init__(self, detail):
        super().__init__(detail, status.HTTP_400_BAD_REQUEST)
