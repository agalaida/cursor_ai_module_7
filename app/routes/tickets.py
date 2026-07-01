from datetime import datetime, timezone, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from marshmallow import ValidationError as MarshmallowError

from app.extensions import db
from app.models.ticket import Ticket, VALID_TRANSITIONS
from app.models.comment import Comment
from app.models.assignment import Assignment
from app.schemas.ticket import (
    TicketSchema, TicketUpdateSchema, StatusUpdateSchema, PriorityUpdateSchema
)
from app.schemas.comment import CommentSchema
from app.utils.auth import get_current_user, role_required
from app.utils.errors import (
    ValidationError, NotFoundException, ForbiddenException
)
from app.utils.sanitize import sanitize
from app.utils.ticket_number import generate_ticket_number
from app.notifications import (
    notify_ticket_created, notify_status_changed, notify_comment_added
)

tickets_bp = Blueprint('tickets', __name__)

ticket_schema = TicketSchema()
ticket_update_schema = TicketUpdateSchema()
status_update_schema = StatusUpdateSchema()
priority_update_schema = PriorityUpdateSchema()
comment_schema = CommentSchema()


def _check_ticket_access(ticket, user):
    if user.role == 'admin':
        return
    if user.role == 'agent':
        if ticket.assigned_to_id != user.id:
            unassigned = ticket.assigned_to_id is None
            if not unassigned:
                raise ForbiddenException('You can only access your assigned tickets.')
        return
    # customer
    if ticket.customer_email != user.email:
        raise ForbiddenException('You can only access your own tickets.')


@tickets_bp.route('/tickets', methods=['GET'])
@jwt_required()
def list_tickets():
    """
    List tickets (filtered by role and query params)
    ---
    tags: [Tickets]
    security:
      - Bearer: []
    parameters:
      - {name: status, in: query, type: string}
      - {name: priority, in: query, type: string}
      - {name: category, in: query, type: string}
      - {name: page, in: query, type: integer, default: 1}
      - {name: per_page, in: query, type: integer, default: 20}
    responses:
      200:
        description: Paginated list of tickets
    """
    user = get_current_user()
    query = Ticket.query

    if user.role == 'customer':
        query = query.filter_by(customer_email=user.email)
    elif user.role == 'agent':
        query = query.filter(
            (Ticket.assigned_to_id == user.id) | (Ticket.assigned_to_id.is_(None))
        )

    status = request.args.get('status')
    priority = request.args.get('priority')
    category = request.args.get('category')
    if status:
        query = query.filter_by(status=status)
    if priority:
        query = query.filter_by(priority=priority)
    if category:
        query = query.filter_by(category=category)

    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    pagination = query.order_by(Ticket.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'tickets': [t.to_dict() for t in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
    }), 200


@tickets_bp.route('/tickets', methods=['POST'])
@jwt_required()
def create_ticket():
    """
    Create a new support ticket
    ---
    tags: [Tickets]
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [subject, description, customer_email]
          properties:
            subject: {type: string}
            description: {type: string}
            priority: {type: string, enum: [low, medium, high, urgent]}
            category: {type: string, enum: [technical, billing, general, feature_request]}
            customer_email: {type: string}
    responses:
      201:
        description: Ticket created
    """
    try:
        data = ticket_schema.load(sanitize(request.get_json() or {}))
    except MarshmallowError as e:
        raise ValidationError(errors=e.messages)

    ticket = Ticket(
        ticket_number=generate_ticket_number(),
        subject=data['subject'],
        description=data['description'],
        priority=data.get('priority', 'medium'),
        category=data.get('category', 'general'),
        customer_email=data['customer_email'],
        status='open',
    )
    db.session.add(ticket)
    db.session.commit()
    notify_ticket_created(ticket)

    return jsonify(ticket.to_dict()), 201


@tickets_bp.route('/tickets/<int:ticket_id>', methods=['GET'])
@jwt_required()
def get_ticket(ticket_id):
    """
    Get a single ticket
    ---
    tags: [Tickets]
    security:
      - Bearer: []
    parameters:
      - {name: ticket_id, in: path, type: integer, required: true}
    responses:
      200:
        description: Ticket detail
      404:
        description: Not found
    """
    user = get_current_user()
    ticket = Ticket.query.get(ticket_id)
    if not ticket:
        raise NotFoundException('Ticket not found.')
    _check_ticket_access(ticket, user)
    return jsonify(ticket.to_dict()), 200


@tickets_bp.route('/tickets/<int:ticket_id>', methods=['PUT'])
@jwt_required()
def update_ticket(ticket_id):
    """
    Update ticket fields (agent/admin)
    ---
    tags: [Tickets]
    security:
      - Bearer: []
    parameters:
      - {name: ticket_id, in: path, type: integer, required: true}
    responses:
      200:
        description: Updated ticket
    """
    user = get_current_user()
    if user.role not in ('agent', 'admin'):
        raise ForbiddenException()
    ticket = Ticket.query.get(ticket_id)
    if not ticket:
        raise NotFoundException('Ticket not found.')

    try:
        data = ticket_update_schema.load(sanitize(request.get_json() or {}), partial=True)
    except MarshmallowError as e:
        raise ValidationError(errors=e.messages)

    for field, value in data.items():
        setattr(ticket, field, value)
    ticket.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    return jsonify(ticket.to_dict()), 200


@tickets_bp.route('/tickets/<int:ticket_id>', methods=['DELETE'])
@role_required('admin')
def delete_ticket(ticket_id):
    """
    Delete a ticket (admin only)
    ---
    tags: [Tickets]
    security:
      - Bearer: []
    parameters:
      - {name: ticket_id, in: path, type: integer, required: true}
    responses:
      200:
        description: Deleted
    """
    ticket = Ticket.query.get(ticket_id)
    if not ticket:
        raise NotFoundException('Ticket not found.')
    db.session.delete(ticket)
    db.session.commit()
    return jsonify({'message': 'Ticket deleted.'}), 200


@tickets_bp.route('/tickets/<int:ticket_id>/status', methods=['PUT'])
@jwt_required()
def update_status(ticket_id):
    """
    Update ticket status
    ---
    tags: [Tickets]
    security:
      - Bearer: []
    parameters:
      - {name: ticket_id, in: path, type: integer, required: true}
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [status]
          properties:
            status: {type: string}
    responses:
      200:
        description: Status updated
    """
    user = get_current_user()
    if user.role not in ('agent', 'admin'):
        raise ForbiddenException()

    ticket = Ticket.query.get(ticket_id)
    if not ticket:
        raise NotFoundException('Ticket not found.')

    try:
        data = status_update_schema.load(request.get_json() or {})
    except MarshmallowError as e:
        raise ValidationError(errors=e.messages)

    new_status = data['status']
    if not ticket.can_transition_to(new_status):
        raise ValidationError(
            message=f'Invalid status transition: {ticket.status} → {new_status}',
            errors={'status': [f'Cannot transition from {ticket.status} to {new_status}.']}
        )

    # closed → reopened only within 7 days (FR-012)
    if ticket.status == 'closed' and new_status == 'reopened':
        if ticket.closed_at:
            closed_at = ticket.closed_at.replace(tzinfo=timezone.utc) if ticket.closed_at.tzinfo is None else ticket.closed_at
            if datetime.now(timezone.utc) - closed_at > timedelta(days=7):
                raise ValidationError(
                    message='Cannot reopen a ticket closed more than 7 days ago.',
                    errors={'status': ['Reopen window has expired (7 days).']}
                )

    ticket.status = new_status
    ticket.updated_at = datetime.now(timezone.utc)
    if new_status == 'resolved':
        ticket.resolved_at = datetime.now(timezone.utc)
    if new_status == 'closed':
        ticket.closed_at = datetime.now(timezone.utc)

    db.session.commit()
    notify_status_changed(ticket, new_status)

    return jsonify(ticket.to_dict()), 200


@tickets_bp.route('/tickets/<int:ticket_id>/priority', methods=['PUT'])
@jwt_required()
def update_priority(ticket_id):
    """
    Update ticket priority (agent/admin, reason required)
    ---
    tags: [Tickets]
    security:
      - Bearer: []
    parameters:
      - {name: ticket_id, in: path, type: integer, required: true}
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [priority, reason]
          properties:
            priority: {type: string, enum: [low, medium, high, urgent]}
            reason: {type: string}
    responses:
      200:
        description: Priority updated
    """
    user = get_current_user()
    if user.role not in ('agent', 'admin'):
        raise ForbiddenException()

    ticket = Ticket.query.get(ticket_id)
    if not ticket:
        raise NotFoundException('Ticket not found.')

    try:
        data = priority_update_schema.load(request.get_json() or {})
    except MarshmallowError as e:
        raise ValidationError(errors=e.messages)

    ticket.priority = data['priority']
    ticket.updated_at = datetime.now(timezone.utc)

    # log the reason as an internal comment
    comment = Comment(
        ticket_id=ticket.id,
        user_id=user.id,
        content=f'Priority changed to {data["priority"]}. Reason: {data["reason"]}',
        is_internal=True,
    )
    db.session.add(comment)
    db.session.commit()

    return jsonify(ticket.to_dict()), 200


@tickets_bp.route('/tickets/<int:ticket_id>/assign', methods=['POST'])
@role_required('admin')
def assign_ticket(ticket_id):
    """
    Assign ticket to an agent (admin only)
    ---
    tags: [Tickets]
    security:
      - Bearer: []
    parameters:
      - {name: ticket_id, in: path, type: integer, required: true}
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [agent_id]
          properties:
            agent_id: {type: integer}
    responses:
      200:
        description: Assigned
    """
    from app.models.user import User
    from app.notifications import notify_ticket_assigned

    ticket = Ticket.query.get(ticket_id)
    if not ticket:
        raise NotFoundException('Ticket not found.')

    agent_id = (request.get_json() or {}).get('agent_id')
    if not agent_id:
        raise ValidationError(errors={'agent_id': ['agent_id is required.']})

    agent = User.query.get(agent_id)
    if not agent or agent.role not in ('agent', 'admin'):
        raise NotFoundException('Agent not found.')

    admin = get_current_user()
    assignment = Assignment(
        ticket_id=ticket.id,
        assigned_to_id=agent.id,
        assigned_by_id=admin.id,
    )
    db.session.add(assignment)

    ticket.assigned_to_id = agent.id
    if ticket.status == 'open':
        ticket.status = 'assigned'
    ticket.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    notify_ticket_assigned(ticket, agent)

    return jsonify(ticket.to_dict()), 200


@tickets_bp.route('/tickets/<int:ticket_id>/history', methods=['GET'])
@jwt_required()
def get_history(ticket_id):
    """
    Get assignment history for a ticket
    ---
    tags: [Tickets]
    security:
      - Bearer: []
    parameters:
      - {name: ticket_id, in: path, type: integer, required: true}
    responses:
      200:
        description: Assignment history
    """
    user = get_current_user()
    if user.role not in ('agent', 'admin'):
        raise ForbiddenException()

    ticket = Ticket.query.get(ticket_id)
    if not ticket:
        raise NotFoundException('Ticket not found.')

    history = Assignment.query.filter_by(ticket_id=ticket_id)\
        .order_by(Assignment.assigned_at.asc()).all()

    return jsonify([h.to_dict() for h in history]), 200


@tickets_bp.route('/tickets/<int:ticket_id>/comments', methods=['POST'])
@jwt_required()
def add_comment(ticket_id):
    """
    Add a comment to a ticket
    ---
    tags: [Tickets]
    security:
      - Bearer: []
    parameters:
      - {name: ticket_id, in: path, type: integer, required: true}
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [content]
          properties:
            content: {type: string}
            is_internal: {type: boolean}
    responses:
      201:
        description: Comment added
    """
    user = get_current_user()
    ticket = Ticket.query.get(ticket_id)
    if not ticket:
        raise NotFoundException('Ticket not found.')
    _check_ticket_access(ticket, user)

    try:
        data = comment_schema.load(sanitize(request.get_json() or {}))
    except MarshmallowError as e:
        raise ValidationError(errors=e.messages)

    is_internal = data.get('is_internal', False)
    if is_internal and user.role == 'customer':
        raise ForbiddenException('Customers cannot post internal comments.')

    comment = Comment(
        ticket_id=ticket.id,
        user_id=user.id,
        content=data['content'],
        is_internal=is_internal,
    )
    db.session.add(comment)
    db.session.commit()
    notify_comment_added(ticket, comment)

    return jsonify(comment.to_dict()), 201


@tickets_bp.route('/tickets/<int:ticket_id>/comments', methods=['GET'])
@jwt_required()
def get_comments(ticket_id):
    """
    Get comments for a ticket
    ---
    tags: [Tickets]
    security:
      - Bearer: []
    parameters:
      - {name: ticket_id, in: path, type: integer, required: true}
    responses:
      200:
        description: List of comments
    """
    user = get_current_user()
    ticket = Ticket.query.get(ticket_id)
    if not ticket:
        raise NotFoundException('Ticket not found.')
    _check_ticket_access(ticket, user)

    query = Comment.query.filter_by(ticket_id=ticket_id)
    if user.role == 'customer':
        query = query.filter_by(is_internal=False)

    comments = query.order_by(Comment.created_at.asc()).all()
    return jsonify([c.to_dict() for c in comments]), 200
