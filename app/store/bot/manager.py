import typing
from random import randint
from logging import getLogger

from app.store.bot.image_app import create_image
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
                    "try_start_game", "try_players_ready", "players_answer",
                    "tag_user", "finished"
            ):
                msg = update.object.body
                await self.app.store.vk_api.send_message(
                    Message(
                        peer_id=update.object.peer_id,
                        text=msg,
                        keyboard=keyboard,
                        attachment=None
                    )
                )
            elif update.object.event_type == "get_answer":
                photo = await self.app.store.vk_api.get_photo(
                    update=update,
                    image_path=f"assets/images/answer{randint(1, 3)}.png"
                )

                await self.app.store.vk_api.send_message(
                    Message(
                        peer_id=update.object.peer_id,
                        text="",
                        keyboard=keyboard,
                        attachment=f"photo{photo['owner_id']}_{photo['id']}"
                    )
                )

            elif update.object.event_type in ("get_question", "players_ready"):
                photo = await self.app.store.vk_api.get_photo(
                    update=update,
                    image_path=f"assets/images/question.png"
                )
                await self.app.store.vk_api.send_message(
                    Message(
                        peer_id=update.object.peer_id,
                        text="❓ Внимание! Вопрос!%0A%0A"
                             "❗ У вас есть 1 минута на обсуждение и 30 секунд на ответ. " 
                             "Отвечает игрок, которого выберет капитан%0A%0A"
                             "💬 Формат ответа: /answer <ответ>",
                        keyboard=keyboard,
                        attachment=f"photo{photo['owner_id']}_{photo['id']}"
                    )
                )
