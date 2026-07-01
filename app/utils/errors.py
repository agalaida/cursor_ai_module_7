from flask import jsonify


class APIException(Exception):
    status_code = 500
    code = 'INTERNAL_ERROR'

    def __init__(self, message='Internal server error', errors=None):
        super().__init__(message)
        self.message = message
        self.errors = errors or {}

    def to_dict(self):
        return {
            'status': 'error',
            'message': self.message,
            'code': self.code,
            'errors': self.errors,
        }


class ValidationError(APIException):
    status_code = 400
    code = 'VALIDATION_ERROR'

    def __init__(self, message='Validation failed', errors=None):
        super().__init__(message, errors)


class UnauthorizedException(APIException):
    status_code = 401
    code = 'UNAUTHORIZED'

    def __init__(self, message='Authentication required'):
        super().__init__(message)


class ForbiddenException(APIException):
    status_code = 403
    code = 'FORBIDDEN'

    def __init__(self, message='Insufficient permissions'):
        super().__init__(message)


class NotFoundException(APIException):
    status_code = 404
    code = 'NOT_FOUND'

    def __init__(self, message='Resource not found'):
        super().__init__(message)


class ConflictException(APIException):
    status_code = 409
    code = 'CONFLICT'

    def __init__(self, message='Conflicting resource'):
        super().__init__(message)


def handle_api_exception(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response
