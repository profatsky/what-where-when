import os.path
import typing
from dataclasses import dataclass

import yaml

if typing.TYPE_CHECKING:
    from app.web.app import Application

base_config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)).replace("app\\web", ""), "config.yml")


@dataclass
class SessionConfig:
    key: str


@dataclass
class AdminConfig:
    email: str
    password: str


@dataclass
class BotConfig:
    token: str
    group_id: int


@dataclass
class DatabaseConfig:
    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: str = "postgres"
    database: str = "project"


@dataclass
class Config:
    admin: AdminConfig
    session: SessionConfig = None
    bot: BotConfig = None
    database: DatabaseConfig = None


def get_sqlalchemy_url(config_path: str = base_config_path):
    with open(config_path, "r") as f:
        cfg = (yaml.safe_load(f))["database"]

    return f"postgresql+asyncpg://{cfg['user']}:{cfg['password']}@{cfg['host']}/{cfg['database']}"


def setup_config(app: "Application", config_path: str = base_config_path):
    with open(config_path, "r") as f:
        raw_config = yaml.safe_load(f)

    app.config = Config(
        session=SessionConfig(
            key=raw_config["session"]["key"],
        ),
        admin=AdminConfig(
            email=raw_config["admin"]["email"],
            password=raw_config["admin"]["password"],
        ),
        bot=BotConfig(
            token=raw_config["bot"]["token"],
            group_id=raw_config["bot"]["group_id"],
        ),
        database=DatabaseConfig(**raw_config["database"]),
    )
