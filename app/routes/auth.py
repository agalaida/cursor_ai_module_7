from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from marshmallow import ValidationError as MarshmallowError

from app.extensions import db, limiter
from app.models.user import User
from app.schemas.user import UserSchema, LoginSchema
from app.utils.errors import ConflictException, UnauthorizedException, ValidationError
from app.utils.sanitize import sanitize

auth_bp = Blueprint('auth', __name__)

user_schema = UserSchema()
login_schema = LoginSchema()


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user
    ---
    tags: [Auth]
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [name, email, password]
          properties:
            name: {type: string, example: John Doe}
            email: {type: string, example: john@example.com}
            password: {type: string, example: secret123}
            role: {type: string, enum: [customer, agent, admin]}
    responses:
      201:
        description: User created
      400:
        description: Validation error
      409:
        description: Email already registered
    """
    try:
        data = user_schema.load(sanitize(request.get_json() or {}))
    except MarshmallowError as e:
        raise ValidationError(errors=e.messages)

    if User.query.filter_by(email=data['email']).first():
        raise ConflictException('Email is already registered.')

    user = User(
        name=data['name'],
        email=data['email'],
        role=data.get('role', 'customer'),
        availability_status=data.get('availability_status', 'available'),
        expertise_areas=data.get('expertise_areas', []),
    )
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully.', 'user': user.to_dict()}), 201


@auth_bp.route('/login', methods=['POST'])
@limiter.limit('10 per minute')
def login():
    """
    Login and receive a JWT token
    ---
    tags: [Auth]
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [email, password]
          properties:
            email: {type: string}
            password: {type: string}
    responses:
      200:
        description: JWT access token
      401:
        description: Invalid credentials
    """
    try:
        data = login_schema.load(request.get_json() or {})
    except MarshmallowError as e:
        raise ValidationError(errors=e.messages)

    user = User.query.filter_by(email=data['email']).first()
    if not user or not user.check_password(data['password']):
        raise UnauthorizedException('Invalid email or password.')

    token = create_access_token(identity=str(user.id))
    return jsonify({'access_token': token, 'user': user.to_dict()}), 200


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    Logout (client must discard the token)
    ---
    tags: [Auth]
    security:
      - Bearer: []
    responses:
      200:
        description: Logged out
    """
    return jsonify({'message': 'Logged out successfully.'}), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    """
    Get current user info
    ---
    tags: [Auth]
    security:
      - Bearer: []
    responses:
      200:
        description: Current user
    """
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict()), 200
