from marshmallow import Schema, fields


class QuestionSchema(Schema):
    id = fields.Int(required=False)
    title = fields.Str(required=True)
    answer_desc = fields.Str(required=True)
    author_id = fields.Str(required=False)
    is_approved = fields.Boolean(required=False)
    answers = fields.Nested("AnswerSchema", many=True, required=True)


class QuestionSimpleSchema(Schema):
    id = fields.Int(required=False)
    is_approved = fields.Boolean(required=False)


class QuestionIdSchema(Schema):
    id = fields.Int(required=True)


class ListQuestionSchema(Schema):
    questions = fields.Nested("QuestionSchema", many=True)


class AnswerSchema(Schema):
    title = fields.Str(required=True)


class GameIdSchema(Schema):
    id = fields.Int(required=False)


class GameSchema(Schema):
    id = fields.Int(required=True)
    chat_id = fields.Int(required=True)
    capitan_id = fields.Int(required=True)
    bot_score = fields.Int(required=True)
    players_score = fields.Int(required=True)
    is_finished = fields.Int(required=True)
    questions = fields.Nested("QuestionSchema", many=True)
    players = fields.Nested("UserSchema", many=True)


class ListGameSchema(Schema):
    games = fields.Nested("GameSchema", many=True)


class UserSchema(Schema):
    id = fields.Int(required=True)
    vk_id = fields.Int(required=True)


class UserIdSchema(Schema):
    id = fields.Int(required=False)


class ListUserSchema(Schema):
    users = fields.Nested("UserSchema", many=True)


class ChatIdSchema(Schema):
    id = fields.Int(required=False)


class ChatSchema(Schema):
    id = fields.Int(required=True)
    vk_id = fields.Int(required=True)


class ChatListSchema(Schema):
    chats = fields.Nested("ChatSchema", many=True)
