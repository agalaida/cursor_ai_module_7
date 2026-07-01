import csv
import io
from datetime import datetime, timezone
from flask import Blueprint, jsonify, request, Response

from app.models.ticket import Ticket
from app.models.user import User
from app.utils.auth import role_required

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/dashboard', methods=['GET'])
@role_required('admin')
def dashboard():
    """
    Admin dashboard metrics
    ---
    tags: [Admin]
    security:
      - Bearer: []
    responses:
      200:
        description: Dashboard metrics
    """
    statuses = ['open', 'assigned', 'in_progress', 'waiting', 'resolved', 'closed', 'reopened']
    by_status = {s: Ticket.query.filter_by(status=s).count() for s in statuses}

    priorities = ['low', 'medium', 'high', 'urgent']
    by_priority = {p: Ticket.query.filter_by(priority=p).count() for p in priorities}

    categories = ['technical', 'billing', 'general', 'feature_request']
    by_category = {c: Ticket.query.filter_by(category=c).count() for c in categories}

    resolved = Ticket.query.filter(Ticket.resolved_at.isnot(None)).all()
    avg_resolution = None
    if resolved:
        durations = [
            (t.resolved_at - t.created_at).total_seconds() / 3600
            for t in resolved
            if t.resolved_at and t.created_at
        ]
        avg_resolution = round(sum(durations) / len(durations), 2) if durations else None

    return jsonify({
        'tickets_by_status': by_status,
        'tickets_by_priority': by_priority,
        'tickets_by_category': by_category,
        'average_resolution_hours': avg_resolution,
        'total_tickets': Ticket.query.count(),
        'total_agents': User.query.filter_by(role='agent').count(),
    }), 200


@admin_bp.route('/reports/tickets', methods=['GET'])
@role_required('admin')
def report_tickets():
    """
    Ticket volume report
    ---
    tags: [Admin]
    security:
      - Bearer: []
    responses:
      200:
        description: Ticket report
    """
    tickets = Ticket.query.order_by(Ticket.created_at.desc()).limit(500).all()
    return jsonify([t.to_dict() for t in tickets]), 200


@admin_bp.route('/reports/agents', methods=['GET'])
@role_required('admin')
def report_agents():
    """
    Agent performance report
    ---
    tags: [Admin]
    security:
      - Bearer: []
    responses:
      200:
        description: Agent performance
    """
    agents = User.query.filter_by(role='agent').all()
    result = []
    for agent in agents:
        open_count = Ticket.query.filter_by(
            assigned_to_id=agent.id
        ).filter(Ticket.status.notin_(['closed', 'resolved'])).count()
        resolved_count = Ticket.query.filter_by(
            assigned_to_id=agent.id, status='resolved'
        ).count() + Ticket.query.filter_by(
            assigned_to_id=agent.id, status='closed'
        ).count()
        result.append({
            **agent.to_dict(),
            'open_tickets': open_count,
            'resolved_tickets': resolved_count,
        })
    return jsonify(result), 200


@admin_bp.route('/reports/sla', methods=['GET'])
@role_required('admin')
def report_sla():
    """
    SLA compliance report
    ---
    tags: [Admin]
    security:
      - Bearer: []
    responses:
      200:
        description: SLA compliance
    """
    from app.models.ticket import SLA_HOURS
    tickets = Ticket.query.filter(Ticket.resolved_at.isnot(None)).all()
    compliant = 0
    breached = 0
    for ticket in tickets:
        sla = SLA_HOURS.get(ticket.priority, {})
        resolution_hours = sla.get('resolution', 120)
        if ticket.resolved_at and ticket.created_at:
            actual = (ticket.resolved_at - ticket.created_at).total_seconds() / 3600
            if actual <= resolution_hours:
                compliant += 1
            else:
                breached += 1
    total = compliant + breached
    return jsonify({
        'compliant': compliant,
        'breached': breached,
        'total_resolved': total,
        'compliance_rate': round(compliant / total * 100, 2) if total else None,
    }), 200


@admin_bp.route('/reports/export', methods=['POST'])
@role_required('admin')
def export_report():
    """
    Export tickets to CSV
    ---
    tags: [Admin]
    security:
      - Bearer: []
    responses:
      200:
        description: CSV file
    """
    tickets = Ticket.query.order_by(Ticket.created_at.desc()).all()
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        'id', 'ticket_number', 'subject', 'status', 'priority',
        'category', 'customer_email', 'assigned_to_id', 'created_at',
    ])
    writer.writeheader()
    for t in tickets:
        writer.writerow({
            'id': t.id,
            'ticket_number': t.ticket_number,
            'subject': t.subject,
            'status': t.status,
            'priority': t.priority,
            'category': t.category,
            'customer_email': t.customer_email,
            'assigned_to_id': t.assigned_to_id,
            'created_at': t.created_at.isoformat(),
        })
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=tickets.csv'},
    )
