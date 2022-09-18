from sqlalchemy import Table, Column, String, Integer, ForeignKey, Boolean, TIMESTAMP
from sqlalchemy.orm import relationship

from app.game.dataclasses import Game, Chat, User, Question, Answer
from app.store.database.sqlalchemy_base import db


class QuestionModel(db):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True)
    title = Column(String, unique=True, nullable=False)
    answer_desc = Column(String, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
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
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)

    def to_dc(self):
        return Answer(
            title=self.title
        )


class GameModel(db):
    __tablename__ = "games"
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"), nullable=False, index=True)
    capitan_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True, index=True)
    current_question = Column(Integer, ForeignKey("questions.id", ondelete="SET NULL"), nullable=True, index=True)
    respondent_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=True, index=True)
    question_time = Column(TIMESTAMP, nullable=True)
    bot_score = Column(Integer, default=0, nullable=False)
    players_score = Column(Integer, default=0, nullable=False)
    is_started = Column(Boolean, default=False, nullable=False)
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
            respondent_id=self.respondent_id,
            current_question=self.current_question,
            question_time=self.question_time,
            bot_score=self.bot_score,
            players_score=self.players_score,
            is_started=self.is_started,
            is_finished=self.is_finished,
            questions=self.questions,
            players=self.players
        )


class ChatModel(db):
    __tablename__ = "chats"
    id = Column(Integer, primary_key=True)
    vk_id = Column(Integer, nullable=False, unique=True)

    def to_dc(self):
        return Chat(
            id=self.id,
            vk_id=self.vk_id
        )


class UserModel(db):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    vk_id = Column(Integer, nullable=False, unique=True)
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
