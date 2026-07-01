from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.utils.errors import ForbiddenException, UnauthorizedException


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            from app.models.user import User
            user_id = int(get_jwt_identity())
            user = User.query.get(user_id)
            if user is None:
                raise UnauthorizedException()
            if user.role not in roles:
                raise ForbiddenException(
                    f'This action requires one of roles: {", ".join(roles)}'
                )
            return f(*args, **kwargs)
        return wrapper
    return decorator


def get_current_user():
    from app.models.user import User
    user_id = int(get_jwt_identity())
    return User.query.get(user_id)
