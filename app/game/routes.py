from typing import TYPE_CHECKING

from app.game.views import QuestionAddView, QuestionListView, QuestionApproveView, QuestionDeleteView, GameListView, \
    UserListView, ChatListView

if TYPE_CHECKING:
    from app.web.app import Application


def setup_routes(app: "Application"):
    app.router.add_view("/game.add_question", QuestionAddView)
    app.router.add_view("/game.list_questions", QuestionListView)
    app.router.add_view("/game.approve_question", QuestionApproveView)
    app.router.add_view("/game.delete_question", QuestionDeleteView)
    app.router.add_view("/game.list_games", GameListView)
    app.router.add_view("/game.list_users", UserListView)
    app.router.add_view("/game.list_chats", ChatListView)
