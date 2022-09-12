from dataclasses import dataclass
from typing import Optional

from sqlalchemy import Table, Column, String, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from app.store.database.sqlalchemy_base import db


@dataclass
class Question:
    id: int
    title: str
    answer_desc: str
    answers: list["Answer"]
    is_approved: bool
    author_id: Optional[int]


@dataclass
class Answer:
    title: int


@dataclass
class User:
    id: int
    vk_id: int


@dataclass
class Game:
    id: int
    chat_id: int
    capitan_id: int
    bot_score: int
    players_score: int
    is_finished: bool
    questions: list["Question"]
    players: list["User"]


@dataclass
class Chat:
    id: int
    vk_id: int


class QuestionModel(db):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True)
    title = Column(String, unique=True, nullable=False)
    answer_desc = Column(String, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    is_approved = Column(Boolean, default=False, nullable=False)
    answers = relationship("AnswerModel")

    def to_dc(self):
        return Question(
            id=self.id,
            title=self.title,
            author_id=self.author_id,
            answer_desc=self.answer_desc,
            is_approved=self.is_approved,
            answers=self.answers
        )


class AnswerModel(db):
    __tablename__ = "answers"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)

    def to_dc(self):
        return Answer(
            title=self.title
        )


class GameModel(db):
    __tablename__ = "games"
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    capitan_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    bot_score = Column(Integer, default=0, nullable=False)
    players_score = Column(Integer, default=0, nullable=False)
    is_finished = Column(Boolean, default=False, nullable=False)
    questions = relationship(
        "QuestionModel",
        secondary="games_questions"
    )
    players = relationship(
        "UserModel",
        secondary="games_users"
    )

    def to_dc(self):
        return Game(
            id=self.id,
            chat_id=self.chat_id,
            capitan_id=self.capitan_id,
            bot_score=self.bot_score,
            players_score=self.players_score,
            is_finished=self.is_finished,
            questions=self.questions,
            players=self.players
        )


class ChatModel(db):
    __tablename__ = "chats"
    id = Column(Integer, primary_key=True)
    vk_id = Column(Integer, nullable=False)

    def to_dc(self):
        return Chat(
            id=self.id,
            vk_id=self.vk_id
        )


class UserModel(db):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    vk_id = Column(Integer, nullable=False)
    authored_questions = relationship(
        "QuestionModel",
        primaryjoin="and_(UserModel.id == QuestionModel.author_id, "
        "QuestionModel.is_approved == True)"
    )

    def to_dc(self):
        return User(
            id=self.id,
            vk_id=self.vk_id
        )


games_users = Table(
    "games_users",
    db.metadata,
    Column("game_id", Integer, ForeignKey("games.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
)

games_questions = Table(
    "games_questions",
    db.metadata,
    Column("game_id", Integer, ForeignKey("games.id", ondelete="CASCADE"), primary_key=True),
    Column("question_id", Integer, ForeignKey("questions.id", ondelete="CASCADE"), primary_key=True)
)
