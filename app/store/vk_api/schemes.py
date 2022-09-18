from marshmallow import Schema, fields


class ActionSchema(Schema):
    type = fields.Str(required=True)
    label = fields.Str(required=True)
    payload = fields.Str(required=False)


class ButtonSchema(Schema):
    action = fields.Nested(ActionSchema, required=True)


class KeyboardSchema(Schema):
    one_time = fields.Bool(required=True)
    buttons = fields.List(fields.Nested(ButtonSchema, required=True, many=True))
