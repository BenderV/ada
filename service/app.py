from flask import Flask, request
from flask_socketio import SocketIO

socketio = SocketIO(cors_allowed_origins="*")


def create_app():
    app = Flask(__name__)
    app.config["JSON_SORT_KEYS"] = False

    from ai.api import api as ai_api
    from back.api import api as back_api
    from chat.api import api as chat_api
    from chat.cli import chat_cli

    app.register_blueprint(chat_api)
    app.register_blueprint(back_api)
    app.register_blueprint(ai_api)
    app.register_blueprint(chat_cli)

    socketio.init_app(app)
    return app
