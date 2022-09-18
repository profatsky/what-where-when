from dataclasses import dataclass
from typing import Optional


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
    respondent_id: int
    current_question: int
    question_time: str
    bot_score: int
    players_score: int
    is_started: bool
    is_finished: bool
    questions: list["Question"]
    players: list["User"]


@dataclass
class Chat:
    id: int
    vk_id: int
