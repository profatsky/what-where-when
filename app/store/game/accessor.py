from datetime import datetime
from random import shuffle
from typing import Optional

from sqlalchemy import select, update, delete, and_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import joinedload, subqueryload
from sqlalchemy.sql.expression import func

from app.game.dataclasses import Question, Answer, Game, User, Chat
from app.game.models import QuestionModel, AnswerModel, GameModel, UserModel, ChatModel, games_users, games_questions
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
        if is_approved:
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

    async def get_games_list(
            self,
            game_id: int = None,
            chat_id: int = None,
            is_started: bool = None,
            is_finished: bool = None
    ) -> list[Game] | None:
        query = select(GameModel)
        if game_id:
            query = query.where(GameModel.id == int(game_id))
        if chat_id:
            query = query.where(GameModel.chat_id == int(chat_id))
        if is_started is not None:
            query = query.where(GameModel.is_started == is_started)
        if is_finished is not None:
            query = query.where(GameModel.is_finished == is_finished)
        async with self.app.database.session() as session:
            result = await session.execute(
                query
                .options(joinedload(GameModel.players))
                .options(joinedload(GameModel.questions))
                .options(subqueryload(GameModel.questions, QuestionModel.answers))
            )

        games_list = [game.to_dc() for game in result.scalars().unique().all()]
        return games_list

    async def get_users_list(self, user_id: int = None, vk_user_id: int = None) -> list[User] | None:
        query = select(UserModel)
        if user_id:
            query = query.where(UserModel.id == int(user_id))
        if vk_user_id:
            query = query.where(UserModel.vk_id == int(vk_user_id))
        async with self.app.database.session() as session:
            result = await session.execute(
                query
            )
        users_list = [user.to_dc() for user in result.scalars().all()]
        return users_list

    async def get_chats_list(self, chat_id: int = None, vk_id: int = None) -> list[Chat] | None:
        query = select(ChatModel)
        if chat_id:
            query = query.where(ChatModel.id == int(chat_id))
        if vk_id:
            query = query.where(ChatModel.vk_id == int(vk_id))
        async with self.app.database.session() as session:
            result = await session.execute(
                query
            )
        chats_list = [chat.to_dc() for chat in result.scalars().all()]
        return chats_list

    async def add_new_chat(self, vk_chat_id: int) -> Chat | None:
        new_chat = ChatModel(vk_id=vk_chat_id)
        insert_stmt = insert(ChatModel).values(vk_id=vk_chat_id)
        do_nothing_stm = insert_stmt.on_conflict_do_nothing(index_elements=["vk_id"])
        async with self.app.database.session.begin() as session:
            await session.execute(do_nothing_stm)
        return new_chat.to_dc()

    async def create_new_game(self, chat_id: int) -> None:
        chat: Chat = (await self.get_chats_list(vk_id=chat_id))[0]
        new_game = GameModel(chat_id=chat.id)
        async with self.app.database.session.begin() as session:
            session.add(new_game)

    async def add_new_user(self, vk_id: int) -> User | None:
        new_user = UserModel(vk_id=vk_id)
        insert_stmt = insert(UserModel).values(vk_id=vk_id)
        do_nothing_stm = insert_stmt.on_conflict_do_nothing(index_elements=["vk_id"])
        async with self.app.database.session.begin() as session:
            await session.execute(do_nothing_stm)
        return new_user.to_dc()

    async def get_game_by_vk_id(self, vk_chat_id: int, is_started: bool = None,
                                is_finished: bool = None) -> Game | None:
        chat: Chat = (await self.get_chats_list(vk_id=vk_chat_id))[0]
        game: list[Game] | None = await self.get_games_list(
            chat_id=chat.id,
            is_started=is_started,
            is_finished=is_finished
        )
        if game:
            return game[0]

    async def add_new_player(self, vk_user_id: int, vk_chat_id: int) -> User | None:
        game: Game | None = await self.get_game_by_vk_id(vk_chat_id, is_started=False, is_finished=False)
        user: User = (await self.get_users_list(vk_user_id=vk_user_id))[0]
        if user.id not in [player.id for player in game.players]:
            async with self.app.database.session.begin() as session:
                await session.execute(
                    insert(games_users).values(game_id=game.id, user_id=user.id)
                )
            return user

    async def choose_capitan(self, vk_chat_id: int) -> User:
        game: Game = await self.get_game_by_vk_id(
            vk_chat_id,
            is_started=True,
            is_finished=False
        )
        players = game.players[:]
        shuffle(players)
        user: User = (await self.get_users_list(vk_user_id=players[0].vk_id))[0]
        async with self.app.database.session.begin() as session:
            await session.execute(
                update(GameModel)
                .where(GameModel.chat_id == game.chat_id)
                .values(capitan_id=user.id)
            )
        return user

    async def get_capitan(self, vk_chat_id: int) -> User:
        game: Game = await self.get_game_by_vk_id(
            vk_chat_id,
            is_started=True,
            is_finished=False
        )
        user: User = (await self.get_users_list(user_id=game.capitan_id))[0]
        return user

    async def start_game(self, vk_chat_id: int) -> None:
        game: Game = await self.get_game_by_vk_id(vk_chat_id, is_started=False, is_finished=False)
        async with self.app.database.session.begin() as session:
            await session.execute(
                update(GameModel)
                .where(and_(GameModel.id == game.id, GameModel.is_finished == False))
                .values(is_started=True)
            )

    async def get_question_for_game(self, vk_chat_id: int) -> Question:
        game: Game = await self.get_game_by_vk_id(vk_chat_id, is_started=True, is_finished=False)
        while True:
            async with self.app.database.session() as session:
                new_question: QuestionModel = await session.execute(
                    select(QuestionModel)
                    .where(QuestionModel.is_approved == True)
                    .options(joinedload(QuestionModel.answers))
                    .order_by(func.random()).limit(1)
                )
            new_question: Question = new_question.scalar().to_dc()
            if new_question.title not in [question.to_dc().title for question in game.questions]:
                break

        async with self.app.database.session.begin() as session:
            await session.execute(
                insert(games_questions)
                .values(game_id=game.id, question_id=new_question.id)
            )
            await session.execute(
                update(GameModel)
                .where(GameModel.id == game.id)
                .values(question_time=datetime.now(), current_question=new_question.id)
            )
        return new_question

    async def choose_respondent(self, vk_chat_id: int, vk_user_id: int) -> User | None:
        game: Game = await self.get_game_by_vk_id(vk_chat_id, is_started=True, is_finished=False)
        user: list[User] | None = await self.get_users_list(vk_user_id=vk_user_id)
        if not user or user[0].vk_id not in [player.vk_id for player in game.players]:
            return
        async with self.app.database.session.begin() as session:
            await session.execute(
                update(GameModel)
                .where(
                    and_(
                        GameModel.id == game.id,
                        GameModel.is_started == True,
                        GameModel.is_finished == False
                    )
                )
                .values(respondent_id=user[0].id)
            )
        return user[0]

    async def get_respondent(self, vk_chat_id: int) -> User | None:
        game: Game = await self.get_game_by_vk_id(vk_chat_id, is_started=True, is_finished=False)
        if not game.respondent_id:
            return
        user: User = (await self.get_users_list(user_id=game.respondent_id))[0]
        return user

    async def get_current_question(self, vk_chat_id: int) -> Question:
        game: Game = await self.get_game_by_vk_id(vk_chat_id, is_started=True, is_finished=False)
        question: Question = await self.get_question_by_id(game.current_question)
        return question

    async def check_answer(self, question_id: int) -> list[str]:
        question: Question = await self.get_question_by_id(question_id)
        answers = [answer.to_dc().title.lower() for answer in question.answers]
        return answers

    async def add_score(self, vk_chat_id: int, players_side: bool = False) -> Game:
        game: Game = await self.get_game_by_vk_id(vk_chat_id, is_started=True, is_finished=False)
        game.players_score += players_side
        game.bot_score += (not players_side)
        async with self.app.database.session.begin() as session:
            await session.execute(
                update(GameModel)
                .where(
                    and_(
                        GameModel.id == game.id,
                        GameModel.is_started == True,
                        GameModel.is_finished == False
                    )
                )
                .values(
                    players_score=game.players_score,
                    bot_score=game.bot_score
                )
            )
        return game

    async def finish_game(self, vk_chat_id: int):
        game: Game = await self.get_game_by_vk_id(vk_chat_id, is_started=True, is_finished=False)
        async with self.app.database.session.begin() as session:
            await session.execute(
                update(GameModel)
                .where(
                    and_(
                        GameModel.id == game.id,
                        GameModel.is_started == True,
                        GameModel.is_finished == False
                    )
                )
                .values(is_finished=True)
            )
