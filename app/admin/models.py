from dataclasses import dataclass
from hashlib import sha256
from typing import Optional

from aiohttp_session import Session
from sqlalchemy import Column, String, BigInteger


from app.store.database.sqlalchemy_base import db


@dataclass
class Admin:
    id: int
    email: str
    password: Optional[str] = None

    def is_password_valid(self, password: str):
        return self.password == sha256(password.encode()).hexdigest()

    @classmethod
    def from_session(cls, session: Optional[Session]) -> Optional["Admin"]:
        return cls(id=session["admin"]["id"], email=session["admin"]["email"])


class AdminModel(db):
    __tablename__ = "admins"
    id = Column(BigInteger, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)

    def to_dc(self) -> Admin:
        return Admin(
            id=self.id,
            email=self.email,
            password=self.password
        )
