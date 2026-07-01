import re
from marshmallow import Schema, fields, validate, validates, ValidationError

ROLES = ['customer', 'agent', 'admin']
AVAILABILITY = ['available', 'busy', 'offline']
EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True, validate=validate.Length(min=8))
    role = fields.Str(missing='customer', validate=validate.OneOf(ROLES))
    availability_status = fields.Str(missing='available', validate=validate.OneOf(AVAILABILITY))
    expertise_areas = fields.List(fields.Str(), missing=list)
    created_at = fields.DateTime(dump_only=True)

    @validates('email')
    def validate_email(self, value):
        if not EMAIL_RE.match(value):
            raise ValidationError('Invalid email format.')


class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)
