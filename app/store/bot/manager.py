import typing
from logging import getLogger

from app.store.vk_api.dataclasses import Update, Message, Keyboard, Button, Action

if typing.TYPE_CHECKING:
    from app.web.app import Application


class BotManager:
    def __init__(self, app: "Application"):
        self.app = app
        self.bot = None
        self.logger = getLogger("handler")

    async def handle_updates(self, updates: list[Update]):
        for update in updates:
            keyboard = None

            if update.object.event_type in ("start_game", "join_game"):
                keyboard = Keyboard(
                    one_time=True,
                    buttons=[
                        [
                            Button(
                                action=Action(
                                    type="text",
                                    label="Присоединиться",
                                    payload="{\"game\":\"ready\"}"
                                )
                            )
                        ]
                    ]
                )

            if update.object.event_type in (
                    "invite_bot", "start_game", "join_game", "try_join_game",
                    "try_start_game", "players_ready", "try_players_ready",
                    "tag_user", "answer"
            ):
                msg = update.object.body
                await self.app.store.vk_api.send_message(
                    Message(
                        peer_id=update.object.peer_id,
                        text=msg,
                        keyboard=keyboard
                    )
                )
