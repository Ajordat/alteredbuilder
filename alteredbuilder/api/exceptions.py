from rest_framework.exceptions import APIException


class AlteredBuilderException(APIException):
    detail = None
    status_code = None

    def __init__(self, detail, status_code):
        super().__init__(detail, status_code)
        self.detail = detail
        self.status_code = status_code
