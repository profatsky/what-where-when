from typing import Optional

from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import joinedload, subqueryload

from app.game.models import Question, Answer, QuestionModel, AnswerModel, Game, GameModel, User, UserModel, games_users, \
    Chat, ChatModel
from app.base.base_accessor import BaseAccessor


class GameAccessor(BaseAccessor):
    async def create_question(
            self, title: str, answer_desc: str, answers: list[Answer], author_id: Optional[str], is_approved: bool
    ) -> Question | None:
        new_question = QuestionModel(
            title=title,
            answer_desc=answer_desc,
            author_id=author_id,
            is_approved=is_approved,
            answers=[
                AnswerModel(
                    title=answer.title
                )
                for answer in answers
            ]
        )
        async with self.app.database.session.begin() as session:
            session.add(new_question)

        return new_question.to_dc()

    async def create_answers(self, question_id: int, answers: list[Answer]) -> list[Answer]:
        new_answers = [
            AnswerModel(
                title=answer.title,
                question_id=question_id
            )
            for answer in answers
        ]
        async with self.app.database.session() as session:
            session.add_all(new_answers)
            await session.commit()

        return [answer.to_dc() for answer in new_answers]

    async def get_question_by_title(self, title: str) -> Question | None:
        async with self.app.database.session() as session:
            result = await session.execute(
                select(QuestionModel)
                .where(QuestionModel.title == title)
                .options(joinedload(QuestionModel.answers))
            )

        obj: QuestionModel | None = result.scalar()
        if obj is None:
            return

        return obj.to_dc()

    async def get_question_by_id(self, id_: int) -> Question | None:
        async with self.app.database.session() as session:
            result = await session.execute(
                select(QuestionModel)
                .where(QuestionModel.id == id_)
                .options(joinedload(QuestionModel.answers))
            )

            obj: QuestionModel | None = result.scalar()
            if obj is None:
                return

            return obj.to_dc()

    async def get_questions_list(self, question_id: int, is_approved: bool) -> list[Question] | None:
        query = select(QuestionModel)
        if question_id:
            query = query.where(QuestionModel.id == int(question_id))
        if is_approved is not None:
            is_approved = True if is_approved == "true" else False
            query = query.where(QuestionModel.is_approved == is_approved)
        async with self.app.database.session() as session:
            result = await session.execute(
                query.options(joinedload(QuestionModel.answers))
            )
        question_list = [question.to_dc() for question in result.scalars().unique().all()]
        return question_list

    async def approve_question(self, id_: int) -> None:
        async with self.app.database.session.begin() as session:
            await session.execute(
                update(QuestionModel)
                .where(QuestionModel.id == id_)
                .values(is_approved=True)
            )

    async def delete_question(self, id_: int) -> None:
        async with self.app.database.session.begin() as session:
            await session.execute(
                delete(QuestionModel)
                .where(QuestionModel.id == id_)
            )

    async def get_games_list(self, game_id: int) -> list[Game] | None:
        query = select(GameModel)
        if game_id:
            query = query.where(GameModel.id == int(game_id))
        async with self.app.database.session() as session:
            result = await session.execute(
                query
                .options(joinedload(GameModel.players))
                .options(joinedload(GameModel.questions))
                .options(subqueryload(GameModel.questions, QuestionModel.answers))
            )

        games_list = [game.to_dc() for game in result.scalars().unique().all()]
        return games_list

    async def get_users_list(self, user_id: int) -> list[User] | None:
        query = select(UserModel)
        if user_id:
            query = query.where(UserModel.id == int(user_id))
        async with self.app.database.session() as session:
            result = await session.execute(
                query
            )
        users_list = [user.to_dc() for user in result.scalars().all()]
        return users_list

    async def get_chats_list(self, chat_id: int) -> list[Chat] | None:
        query = select(ChatModel)
        if chat_id:
            query = query.where(ChatModel.id == int(chat_id))
        async with self.app.database.session() as session:
            result = await session.execute(
                query
            )
        chats_list = [chat.to_dc() for chat in result.scalars().all()]
        return chats_list
