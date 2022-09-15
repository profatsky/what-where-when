from aiohttp.web_exceptions import HTTPConflict, HTTPBadRequest, HTTPNotFound
from aiohttp_apispec import response_schema, request_schema, querystring_schema

from app.game.models import Answer
from app.game.schemes import QuestionSchema, QuestionIdSchema, ListQuestionSchema, QuestionSimpleSchema, GameSchema, \
    GameIdSchema, ListGameSchema, UserSchema, ListUserSchema, UserIdSchema, ChatIdSchema, ChatListSchema
from app.web.app import View
from app.web.mixins import AuthRequiredMixin
from app.web.schemes import OkResponseSchema
from app.web.utils import json_response


class QuestionAddView(AuthRequiredMixin, View):
    @request_schema(QuestionSchema)
    @response_schema(QuestionSchema, 200)
    async def post(self):
        if not self.data["answers"]:
            raise HTTPBadRequest(reason="answers not listed")

        title = self.data["title"]
        if await self.store.game.get_question_by_title(title):
            raise HTTPConflict(reason="This question already exists")

        question = await self.store.game.create_question(
            title=title,
            answer_desc=self.data["answer_desc"],
            author_id=self.data.get("author_id"),
            is_approved=self.data.get("is_approved", False),
            answers=[
                Answer(
                    title=answer["title"]
                ) for answer in self.data["answers"]
            ]
        )

        return json_response(data=QuestionSchema().dump(question))


class QuestionListView(AuthRequiredMixin, View):
    @querystring_schema(QuestionSimpleSchema)
    @response_schema(ListQuestionSchema, 200)
    async def get(self):
        query = self.request.query
        questions = await self.store.game.get_questions_list(query.get("id"), query.get("is_approved"))
        return json_response(ListQuestionSchema().dump({"questions": questions}))


class QuestionApproveView(AuthRequiredMixin, View):
    @request_schema(QuestionIdSchema)
    @response_schema(OkResponseSchema, 200)
    async def post(self):
        if await self.store.game.get_question_by_id(self.data["id"]) is None:
            raise HTTPNotFound(reason="No such question exists")

        await self.store.game.approve_question(self.data["id"])
        return json_response({"result": "Question successfully approved"})


class QuestionDeleteView(AuthRequiredMixin, View):
    @request_schema(QuestionIdSchema)
    @response_schema(OkResponseSchema, 200)
    async def post(self):
        if await self.store.game.get_question_by_id(self.data["id"]) is None:
            raise HTTPNotFound(reason="No such question exists")

        await self.store.game.delete_question(self.data["id"])
        return json_response({"result": "Question successfully deleted"})


class GameListView(AuthRequiredMixin, View):
    @querystring_schema(GameIdSchema)
    @response_schema(ListGameSchema, 200)
    async def get(self):
        games = await self.store.game.get_games_list(self.request.query.get("id"))
        return json_response(ListGameSchema().dump({"games": games}))


class UserListView(AuthRequiredMixin, View):
    @querystring_schema(UserIdSchema)
    @response_schema(ListUserSchema, 200)
    async def get(self):
        users = await self.store.game.get_users_list(self.request.query.get("id"))
        return json_response(ListUserSchema().dump({"users": users}))


class ChatListView(AuthRequiredMixin, View):
    @querystring_schema(ChatIdSchema)
    @response_schema(ChatListSchema, 200)
    async def get(self):
        chats = await self.store.game.get_chats_list(self.request.query.get("id"))
        return json_response(ChatListSchema().dump({"chats": chats}))
