from marshmallow import Schema, fields, validate


class CommentSchema(Schema):
    id = fields.Int(dump_only=True)
    ticket_id = fields.Int(dump_only=True)
    user_id = fields.Int(dump_only=True)
    content = fields.Str(required=True, validate=validate.Length(min=1, max=10000))
    is_internal = fields.Bool(missing=False)
    created_at = fields.DateTime(dump_only=True)
