class BriefmetricsException(Exception):
    pass


class APIException(BriefmetricsException):
    def __init__(self, message, code=400, response=None):
        self.message = message
        self.code = 400
        self.response = response

    def __repr__(self):
        return '%s("%s", code=%d)' % (self.__class__.__name__, self.message, self.code)

    def __str__(self):
        return self.message


class TableShapeError(BriefmetricsException):
    pass


class APIError(APIException):
    pass


class APIControllerError(APIError):
    pass


class LoginRequired(APIException):
    def __init__(self, message=None, next=None):
        APIException.__init__(self, message or 'Login required.', code=403)

        self.next = next

    def next_url(self, request, next=None, service=None):
        query = {'next': next or self.next}
        return request.route_url('account_login', _query=query, service=service or 'google')
