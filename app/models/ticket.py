from datetime import datetime, timezone
from app.extensions import db


VALID_TRANSITIONS = {
    'open':        ['assigned', 'closed'],
    'assigned':    ['in_progress', 'closed'],
    'in_progress': ['waiting', 'resolved', 'closed'],
    'waiting':     ['in_progress'],
    'resolved':    ['closed', 'reopened'],
    'closed':      ['reopened'],
    'reopened':    ['in_progress'],
}

SLA_HOURS = {
    'urgent': {'response': 2,  'resolution': 24},
    'high':   {'response': 4,  'resolution': 48},
    'medium': {'response': 8,  'resolution': 120},
    'low':    {'response': 24, 'resolution': 240},
}


class Ticket(db.Model):
    __tablename__ = 'tickets'

    __table_args__ = (
        db.Index('idx_ticket_status_priority', 'status', 'priority'),
        db.Index('idx_ticket_assigned_status', 'assigned_to_id', 'status'),
        db.Index('idx_ticket_customer_email', 'customer_email'),
    )

    id = db.Column(db.Integer, primary_key=True)
    ticket_number = db.Column(db.String(30), unique=True, nullable=False, index=True)
    subject = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='open')
    priority = db.Column(db.String(20), nullable=False, default='medium')
    category = db.Column(db.String(50), nullable=False, default='general')
    customer_email = db.Column(db.String(120), nullable=False)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))
    resolved_at = db.Column(db.DateTime, nullable=True)
    closed_at = db.Column(db.DateTime, nullable=True)

    comments = db.relationship('Comment', backref='ticket', lazy='dynamic',
                               cascade='all, delete-orphan')
    assignments = db.relationship('Assignment', backref='ticket', lazy='dynamic',
                                  cascade='all, delete-orphan')
    attachments = db.relationship('Attachment', backref='ticket', lazy='dynamic',
                                  cascade='all, delete-orphan')

    def can_transition_to(self, new_status):
        return new_status in VALID_TRANSITIONS.get(self.status, [])

    def to_dict(self):
        return {
            'id': self.id,
            'ticket_number': self.ticket_number,
            'subject': self.subject,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'category': self.category,
            'customer_email': self.customer_email,
            'assigned_to_id': self.assigned_to_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'closed_at': self.closed_at.isoformat() if self.closed_at else None,
        }
