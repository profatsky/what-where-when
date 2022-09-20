import json
import random
import typing
from datetime import datetime
from io import BytesIO
from re import fullmatch
from typing import Optional

import requests
from aiohttp import TCPConnector
from aiohttp.client import ClientSession

from app.base.base_accessor import BaseAccessor
from app.store.bot.image_app import create_image
from app.store.vk_api.dataclasses import Message, Update, UpdateObject
from app.store.vk_api.poller import Poller
from app.store.vk_api.schemes import KeyboardSchema

if typing.TYPE_CHECKING:
    from app.web.app import Application

API_PATH = "https://api.vk.com/method/"


class VkApiAccessor(BaseAccessor):
    def __init__(self, app: "Application", *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        self.session: Optional[ClientSession] = None
        self.key: Optional[str] = None
        self.server: Optional[str] = None
        self.poller: Optional[Poller] = None
        self.ts: Optional[int] = None

    async def connect(self, app: "Application"):
        self.session = ClientSession(connector=TCPConnector(verify_ssl=False))
        try:
            await self._get_long_poll_service()
        except Exception as e:
            self.logger.error("Exception", exc_info=e)
        self.poller = Poller(app.store)
        self.logger.info("start polling")
        await self.poller.start()

    async def disconnect(self, app: "Application"):
        if self.session:
            await self.session.close()
        if self.poller:
            await self.poller.stop()

    @staticmethod
    def _build_query(host: str, method: str, params: dict) -> str:
        url = host + method + "?"
        if "v" not in params:
            params["v"] = "5.131"
        url += "&".join([f"{k}={v}" for k, v in params.items()])
        return url

    async def _get_long_poll_service(self):
        async with self.session.get(
                self._build_query(
                    host=API_PATH,
                    method="groups.getLongPollServer",
                    params={
                        "group_id": self.app.config.bot.group_id,
                        "access_token": self.app.config.bot.token,
                    },
                )
        ) as resp:
            data = (await resp.json())["response"]
            self.logger.info(data)
            self.key = data["key"]
            self.server = data["server"]
            self.ts = data["ts"]
            self.logger.info(self.server)

    async def poll(self):
        async with self.session.get(
                self._build_query(
                    host=self.server,
                    method="",
                    params={
                        "act": "a_check",
                        "key": self.key,
                        "ts": self.ts,
                        "wait": 30,
                    }
                )
        ) as resp:
            data = await resp.json()
            self.ts = data["ts"]
            raw_updates = data.get("updates", [])
            updates = []
            for update in raw_updates:
                if update['type'] == 'message_new':
                    self.logger.info(data)
                    message_text = update["object"]["message"]["text"]
                    body = message_text
                    peer_id = update["object"]["message"]["peer_id"]
                    from_id = update["object"]["message"]["from_id"]
                    # Если пришло сообщение из чата
                    if peer_id != from_id:
                        self.logger.info("Пришло сообщение из чата")

                        # Если пригласили в беседу
                        if (update_action := update["object"]["message"].get("action")) is not None and \
                                update_action["type"] == "chat_invite_user" \
                                and update_action["member_id"] == -self.app.config.bot.group_id:
                            self.logger.info("Пригласили в беседу")
                            event_type = "invite_bot"
                            await self.app.store.game.add_new_chat(vk_chat_id=peer_id)
                            body = "🎈 Приветствую! Я бот для игры «Что? Где? Когда?» Чтобы начать игру выдайте мне " \
                                   "права администратора и напишите /start"

                        # Если создали игру
                        elif message_text == "/start":
                            if not await self.app.store.game.get_game_by_vk_id(
                                    vk_chat_id=peer_id,
                                    is_finished=False
                            ):
                                event_type = "start_game"

                                await self.app.store.game.create_new_game(
                                    chat_id=peer_id
                                )
                                body = "✔ Игра начнется как только будет написано /ready!%0A" \
                                       "Чтобы присоединиться к игре нажмите на кнопку или напишите /join"

                            else:
                                event_type = "try_start_game"

                                body = "❗ Вы не можете начать новую игру, пока не завершилась предыдущая!"

                        # Запуск игры после набора участников
                        elif message_text == "/ready":
                            if await self.app.store.game.get_game_by_vk_id(
                                vk_chat_id=peer_id,
                                is_started=False,
                                is_finished=False
                            ):
                                event_type = "players_ready"

                                await self.app.store.game.start_game(
                                    vk_chat_id=peer_id
                                )

                                capitan_id = await self.app.store.game.choose_capitan(
                                    vk_chat_id=peer_id
                                )
                                info = (await self.app.store.vk_api.get_users_info(capitan_id.vk_id))[0]
                                await self.app.store.vk_api.send_message(
                                    Message(
                                        peer_id=peer_id,
                                        text=f"✔ Игроки готовы, а значит можно начинать!%0A%0A"
                                             f"🧢 Капитан команды - [id{info['id']}|{info['first_name']} "
                                             f"{info['last_name']}]%0A%0A"
                                             f"⏱ В течение 1.5 минуты после каждого вопроса, он должен выбрать "
                                             f"(через обращение @) того, кто отвечает",
                                        keyboard=None,
                                        attachment=None
                                    )
                                )

                                question = await self.app.store.game.get_question_for_game(
                                    vk_chat_id=peer_id
                                )
                                body = f"{question.title}"
                                author = await self.app.store.game.get_author(question)
                                if author:
                                    info = (await self.app.store.vk_api.get_users_info(author.vk_id))[0]
                                    body += f"|{info['first_name']} {info['last_name']}"
                            else:
                                event_type = "try_players_ready"

                                body = "❗ Сейчас вы не можете запустить игру!"

                        # Выбор отвечающего
                        elif fullmatch(r"\[id\d+\|.+]", message_text):
                            event_type = "tag_user"
                            capitan = await self.app.store.game.get_capitan(peer_id)
                            if not capitan:
                                event_type = None
                            elif capitan.vk_id != from_id:
                                body = "❗ Вы не можете выбрать отвечающего, т.к. не являетесь капитаном команды!"
                            elif not await self.app.store.game.choose_respondent(
                                vk_chat_id=peer_id,
                                vk_user_id=int(message_text.split("|")[0][3:])
                            ):
                                body = "❗ Этот игрок не участвует в игре!"
                            else:
                                body = f"На вопрос отвечает {message_text}"

                        # Ответ на вопрос
                        elif fullmatch(r"/answer .+", message_text):
                            event_type = "players_answer"
                            respondent = await self.app.store.game.get_respondent(
                                vk_chat_id=peer_id
                            )
                            if respondent is None or from_id != respondent.vk_id:
                                info = (
                                    await self.app.store.vk_api.get_users_info(from_id)
                                )[0]
                                body = f"❗ [id{info['id']}|{info['first_name']} {info['last_name']}], " \
                                       "Вы не были выбраны в качестве игрока, который должен отвечать!"
                            else:
                                question = await self.app.store.game.get_current_question(vk_chat_id=peer_id)
                                answers = await self.app.store.game.check_answer(question_id=question.id)

                                game = await self.app.store.game.get_game_by_vk_id(
                                    vk_chat_id=peer_id,
                                    is_started=True,
                                    is_finished=False
                                )
                                if (datetime.now() - game.question_time).seconds > 90:
                                    body = f"❌ Прошло более 1.5 минуты. Ответ не засчитан%0A%0A"
                                    game = await self.app.store.game.add_score(
                                        vk_chat_id=peer_id,
                                        players_side=False
                                    )
                                elif message_text[8:].lower() in answers:
                                    game = await self.app.store.game.add_score(
                                        vk_chat_id=peer_id,
                                        players_side=True
                                    )

                                    body = "✔ Это правильный ответ!%0A%0A"

                                else:
                                    game = await self.app.store.game.add_score(
                                        vk_chat_id=peer_id,
                                        players_side=False
                                    )

                                    body = "❌ Это неправильный ответ!%0A%0A"

                                body += f"🙋‍♂️Ваша команда {game.players_score} : 🤖 Бот {game.bot_score}"

                                updates.append(
                                    Update(
                                        type=update['type'],
                                        object=UpdateObject(
                                            id=update['object']['message']['id'],
                                            user_id=from_id,
                                            peer_id=peer_id,
                                            body=body,
                                            event_type=event_type
                                        )
                                    )
                                )

                                body = f"{question.answer_desc}"

                                updates.append(
                                    Update(
                                        type=update['type'],
                                        object=UpdateObject(
                                            id=update['object']['message']['id'],
                                            user_id=from_id,
                                            peer_id=peer_id,
                                            body=body,
                                            event_type="get_answer"
                                        )
                                    )
                                )

                                if 6 in (game.players_score, game.bot_score):
                                    event_type = "finished"
                                    if game.players_score == 6:
                                        body = "%0A%0A🥳 Поздравляю! Вы победили!"
                                    elif game.bot_score == 6:
                                        body = "%0A%0A😕 Увы, вы проиграли!"
                                    await self.app.store.game.finish_game(peer_id)

                                else:
                                    event_type = "get_question"
                                    question = await self.app.store.game.get_question_for_game(
                                        vk_chat_id=peer_id
                                    )
                                    body = f"{question.title}"
                                    author = await self.app.store.game.get_author(question)
                                    if author:
                                        info = (await self.app.store.vk_api.get_users_info(author.vk_id))[0]
                                        body += f"|{info['first_name']} {info['last_name']}"

                        # Если была нажата кнопка "Присоединится" или написали /join
                        elif update["object"]["message"].get("payload") is not None and \
                                update["object"]["message"]["payload"] == "{\"game\":\"ready\"}" or \
                                message_text == "/join":
                            event_type = "join_game"

                            if not await self.app.store.game.get_game_by_vk_id(
                                vk_chat_id=peer_id,
                                is_started=False,
                                is_finished=False
                            ):
                                event_type = "try_join_game"
                                body = "❗ Нельзя присоединится к игре в данный момент"
                            else:
                                await self.app.store.game.add_new_user(
                                    vk_id=from_id
                                )
                                if not await self.app.store.game.add_new_player(
                                    vk_user_id=from_id,
                                    vk_chat_id=peer_id
                                ):
                                    body = "❗ Вы уже присоединились к игре"
                                else:
                                    info = (await self.app.store.vk_api.get_users_info(from_id))[0]
                                    body = f"➕ [id{info['id']}|{info['first_name']} {info['last_name']}] " \
                                           f"присоединился к игре!"

                        else:
                            event_type = "other"

                        updates.append(
                            Update(
                                type=update["type"],
                                object=UpdateObject(
                                    id=update["object"]["message"]["id"],
                                    user_id=from_id,
                                    peer_id=peer_id,
                                    body=body,
                                    event_type=event_type
                                )
                            )
                        )

                    else:
                        # Личка
                        updates.append(
                            Update(
                                type=update['type'],
                                object=UpdateObject(
                                    id=update['object']['message']['id'],
                                    user_id=from_id,
                                    peer_id=peer_id,
                                    body=body,
                                    event_type="personal_msg"
                                )
                            )
                        )
            return updates

    async def send_message(self, message: Message) -> None:
        async with self.session.get(
                self._build_query(
                    API_PATH,
                    "messages.send",
                    params={
                        "peer_id": message.peer_id,
                        "random_id": random.randint(1, 2 ** 32),
                        "message": message.text,
                        "access_token": self.app.config.bot.token,
                        "keyboard": str(json.dumps(KeyboardSchema().dump(message.keyboard))),
                        "attachment": message.attachment
                    },
                )
        ) as resp:
            data = await resp.json()
            self.logger.info(data)

    async def get_users_info(self, user_ids: list[int]):
        async with self.session.get(
            self._build_query(
                API_PATH,
                "users.get",
                params={
                    "access_token": self.app.config.bot.token,
                    "user_ids": user_ids
                }
            )
        ) as resp:
            data = await resp.json()
            return data["response"]

    async def get_messages_upload_server(self, peer_id: int) -> str:
        async with self.session.get(
                self._build_query(
                    API_PATH,
                    "photos.getMessagesUploadServer",
                    params={
                        "access_token": self.app.config.bot.token,
                        "peer_id": peer_id
                    }
                )
        ) as resp:
            data = await resp.json()
            return data["response"]["upload_url"]

    async def save_message_photo(self, photo: BytesIO, server: str, hash_: str) -> None:
        async with self.session.get(
                self._build_query(
                    API_PATH,
                    "photos.saveMessagesPhoto",
                    params={
                        "access_token": self.app.config.bot.token,
                        "photo": photo,
                        "server": server,
                        "hash": hash_
                    }
                )
        ) as resp:
            data = await resp.json()
            return data["response"][0]

    async def get_photo(self, update: Update, image_path: str) -> dict:
        server = await self.app.store.vk_api.get_messages_upload_server(update.object.peer_id)
        body = update.object.body.split("|")
        question = body[0]
        author_name = None
        if len(body) == 2:
            author_name = body[1]
        print("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", body, question, author_name)
        response = requests.post(
            url=server,
            files={"file": (
                "file.png", create_image(
                    image_path=image_path,
                    text=question,
                    author_name=author_name
                )
            )}
        ).json()

        photo = await self.app.store.vk_api.save_message_photo(
            server=response["server"],
            photo=response["photo"],
            hash_=response["hash"]
        )

        return photo
