import re
from marshmallow import Schema, fields, validate, validates, ValidationError

PRIORITIES = ['low', 'medium', 'high', 'urgent']
CATEGORIES = ['technical', 'billing', 'general', 'feature_request']
STATUSES = ['open', 'assigned', 'in_progress', 'waiting', 'resolved', 'closed', 'reopened']
SUBJECT_RE = re.compile(r'^[\w\s\-.,!?:;\'\"()/]+$')


class TicketSchema(Schema):
    id = fields.Int(dump_only=True)
    ticket_number = fields.Str(dump_only=True)
    subject = fields.Str(
        required=True,
        validate=[
            validate.Length(min=5, max=200),
        ]
    )
    description = fields.Str(
        required=True,
        validate=validate.Length(min=20, max=5000)
    )
    priority = fields.Str(missing='medium', validate=validate.OneOf(PRIORITIES))
    category = fields.Str(missing='general', validate=validate.OneOf(CATEGORIES))
    customer_email = fields.Email(required=True)
    status = fields.Str(dump_only=True)
    assigned_to_id = fields.Int(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    resolved_at = fields.DateTime(dump_only=True, allow_none=True)
    closed_at = fields.DateTime(dump_only=True, allow_none=True)

    @validates('subject')
    def validate_subject_chars(self, value):
        if not SUBJECT_RE.match(value):
            raise ValidationError(
                'Subject may only contain letters, digits, spaces, and common punctuation.'
            )


class TicketUpdateSchema(Schema):
    subject = fields.Str(validate=[validate.Length(min=5, max=200)])
    description = fields.Str(validate=validate.Length(min=20, max=5000))
    priority = fields.Str(validate=validate.OneOf(PRIORITIES))
    category = fields.Str(validate=validate.OneOf(CATEGORIES))


class StatusUpdateSchema(Schema):
    status = fields.Str(required=True, validate=validate.OneOf(STATUSES))


class PriorityUpdateSchema(Schema):
    priority = fields.Str(required=True, validate=validate.OneOf(PRIORITIES))
    reason = fields.Str(required=True, validate=validate.Length(min=5))
