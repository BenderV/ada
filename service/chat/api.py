from threading import Lock

from back.models import User
from back.session import session
from chat.datachat import DatabaseChat
from flask import Blueprint
from flask_socketio import emit

api = Blueprint("chat_api", __name__)

from app import socketio

conversation_stop_flags = {}
stop_flag_lock = Lock()
MAX_DATA_SIZE = 4000  # Maximum size of the data to return
CONVERSATION_MAX_ATTEMPT = 10  # Number of attempts to ask the ai before giving up


def user_has_access(user_id: int, database_id: int) -> bool:
    """
    Check if a user has access to a specific database.

    :param user_id: The ID of the user.
    :param database_id: The ID of the database.
    :return: True if the user has access, False otherwise.
    """
    user = session.query(User).filter_by(id=user_id).first()

    if not user:
        return False

    # Assuming you have a many-to-many relationship between User and Database models
    # Replace 'user_databases' with the appropriate attribute name from your User model
    accessible_databases = [db.id for db in user.user_databases]

    return database_id in accessible_databases


@socketio.on("stop")
def handle_stop(conversation_id):
    print("Received stop signal for conversation_id", conversation_id)
    # Stop the query
    with stop_flag_lock:
        if conversation_id in conversation_stop_flags:
            conversation_stop_flags[conversation_id] = True
            emit_status(conversation_id, STATUS.TO_STOP)

        else:
            print(
                f"No active 'ask' process found for conversation_id {conversation_id}"
            )


class STATUS:
    RUNNING = "running"
    CLEAR = "clear"
    TO_STOP = "to_stop"
    ERROR = "error"


def emit_status(conversation_id, status, error=None):
    emit(
        "status",
        {"conversation_id": conversation_id, "status": status, "error": str(error)},
    )


def handle_stop_flag(func):
    def wrapper(*args, **kwargs):
        # Extract the conversation_id from the arguments
        conversation_id = args[2]

        with stop_flag_lock:
            # Avoid running the same query twice
            if conversation_id in conversation_stop_flags:
                # We re-emit the running status to the client
                if conversation_stop_flags[conversation_id]:
                    emit_status(conversation_id, STATUS.TO_STOP)
                else:
                    emit_status(conversation_id, STATUS.RUNNING)
                return

        conversation_stop_flags[conversation_id] = False
        emit_status(conversation_id, STATUS.RUNNING)
        try:
            res = func(*args, **kwargs)
        except Exception as e:
            emit_status(conversation_id, STATUS.ERROR, e)
            raise e
        else:
            emit_status(conversation_id, STATUS.CLEAR)
        finally:
            with stop_flag_lock:
                # Remove the stop flag
                del conversation_stop_flags[conversation_id]

        return res

    return wrapper


@socketio.on("ask")
@handle_stop_flag
def handle_ask(question, conversation_id=None, database_id=None):
    iterator = DatabaseChat(database_id, conversation_id, conversation_stop_flags).ask(
        question
    )
    for message in iterator:
        emit("response", message)
