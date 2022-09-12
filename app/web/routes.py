from aiohttp.web_app import Application


def setup_routes(app: Application):
    from app.admin.routes import setup_routes as admin_setup_routes
    from app.game.routes import setup_routes as game_setup_routes

    admin_setup_routes(app)
    game_setup_routes(app)
