from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError as MarshmallowError

from app.extensions import db
from app.models.user import User
from app.schemas.user import UserSchema
from app.utils.auth import role_required, get_current_user
from app.utils.errors import NotFoundException, ValidationError, ForbiddenException

users_bp = Blueprint('users', __name__)
user_schema = UserSchema()


@users_bp.route('/users', methods=['GET'])
@role_required('admin')
def list_users():
    """
    List all users (admin only)
    ---
    tags: [Users]
    security:
      - Bearer: []
    responses:
      200:
        description: List of users
    """
    users = User.query.all()
    return jsonify([u.to_dict() for u in users]), 200


@users_bp.route('/users/<int:user_id>', methods=['GET'])
@role_required('admin')
def get_user(user_id):
    """
    Get a user by ID (admin only)
    ---
    tags: [Users]
    security:
      - Bearer: []
    parameters:
      - {name: user_id, in: path, type: integer, required: true}
    responses:
      200:
        description: User detail
    """
    user = User.query.get(user_id)
    if not user:
        raise NotFoundException('User not found.')
    return jsonify(user.to_dict()), 200


@users_bp.route('/users/<int:user_id>', methods=['PUT'])
@role_required('admin')
def update_user(user_id):
    """
    Update a user (admin only)
    ---
    tags: [Users]
    security:
      - Bearer: []
    parameters:
      - {name: user_id, in: path, type: integer, required: true}
    responses:
      200:
        description: Updated user
    """
    user = User.query.get(user_id)
    if not user:
        raise NotFoundException('User not found.')

    data = request.get_json() or {}
    allowed = ('name', 'role', 'availability_status', 'expertise_areas')
    for field in allowed:
        if field in data:
            setattr(user, field, data[field])
    db.session.commit()
    return jsonify(user.to_dict()), 200


@users_bp.route('/agents', methods=['GET'])
@role_required('admin')
def list_agents():
    """
    List all agents (admin only)
    ---
    tags: [Users]
    security:
      - Bearer: []
    responses:
      200:
        description: List of agents
    """
    agents = User.query.filter_by(role='agent').all()
    return jsonify([a.to_dict() for a in agents]), 200


@users_bp.route('/agents/<int:agent_id>/tickets', methods=['GET'])
@role_required('admin')
def agent_tickets(agent_id):
    """
    Get all tickets assigned to an agent (admin only)
    ---
    tags: [Users]
    security:
      - Bearer: []
    parameters:
      - {name: agent_id, in: path, type: integer, required: true}
    responses:
      200:
        description: Agent's tickets
    """
    from app.models.ticket import Ticket
    agent = User.query.get(agent_id)
    if not agent:
        raise NotFoundException('Agent not found.')
    tickets = Ticket.query.filter_by(assigned_to_id=agent_id).all()
    return jsonify([t.to_dict() for t in tickets]), 200


@users_bp.route('/agents/<int:agent_id>/availability', methods=['PUT'])
@jwt_required()
def update_availability(agent_id):
    """
    Update agent availability status
    ---
    tags: [Users]
    security:
      - Bearer: []
    parameters:
      - {name: agent_id, in: path, type: integer, required: true}
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [availability_status]
          properties:
            availability_status: {type: string, enum: [available, busy, offline]}
    responses:
      200:
        description: Updated
    """
    current = get_current_user()
    if current.role != 'admin' and current.id != agent_id:
        raise ForbiddenException()

    agent = User.query.get(agent_id)
    if not agent:
        raise NotFoundException('Agent not found.')

    status = (request.get_json() or {}).get('availability_status')
    if status not in ('available', 'busy', 'offline'):
        raise ValidationError(errors={'availability_status': ['Must be available, busy, or offline.']})

    agent.availability_status = status
    db.session.commit()
    return jsonify(agent.to_dict()), 200
