import json
from threading import Lock

from back.datalake import DatalakeFactory
from back.models import Conversation, ConversationMessage, Database, User
from back.session import session
from flask import Blueprint
from flask_socketio import emit

api = Blueprint("chat_api", __name__)

from app import socketio

conversation_stop_flags = {}
stop_flag_lock = Lock()


def extract_sql(text):
    import re

    # Define a regular expression pattern to match the SQL query
    pattern = r"```(sql)?(.*?)```"

    # Use the re.findall() function to extract all matches of the pattern
    matches = re.findall(pattern, text, re.DOTALL)

    try:
        # Print the first match (assuming there is only one SQL query in the text)
        return matches[0][1].strip()
    except IndexError:
        pass


def record_message(**kwargs):
    # change lower_case keys to camelCase keys
    def camel_case(snake_str):
        components = snake_str.split("_")
        return components[0] + "".join(x.title() for x in components[1:])

    kwargs = {camel_case(k): v for k, v in kwargs.items()}
    # Create a new message
    message = ConversationMessage(**kwargs)
    session.add(message)
    session.commit()


def create_conversation(name, databaseId, ownerId):
    # Create conversation object
    conversation = Conversation(
        name=name,
        ownerId="admin",
        databaseId=databaseId,
    )
    session.add(conversation)
    session.commit()
    return conversation


RESULT_TEMPLATE = """Result {len_sample}/{len_total}:
```json
{sample}
```
"""

ERROR_TEMPLATE = """An error occurred while executing the SQL query:
```error
{error}
```
Please correct the query and try again.
"""


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


def emit_status(conversation_id, status):
    emit(
        "status",
        {
            "conversation_id": conversation_id,
            "status": status,
        },
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
            emit_status(conversation_id, STATUS.ERROR)
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
    print("ask:", question, conversation_id, database_id)

    if not conversation_id:
        # TODO: Verify user is allowed to access database
        # if not user_has_access(request.user, database_id):
        #   return {"error": "User does not have access to the requested database"}

        # Create conversation object
        conversation = create_conversation(
            name=question, databaseId=database_id, ownerId="admin"
        )
    else:
        conversation = session.query(Conversation).filter_by(id=conversation_id).first()

    database = conversation.database
    # Add a datalake object to the request
    datalake = DatalakeFactory.create(
        database.engine,
        **database.details,
    )

    question = f"In {datalake.dialect} database; {question}"

    user_question = {
        "conversation_id": conversation.id,
        "content": question,
        "role": "user",
        "display": True,
        "done": False,
    }
    record_message(**user_question)

    def emit_message(content, role="assistant", display=True, done=False, data=None):
        # TODO: record more stuff

        message = {
            "conversation_id": conversation.id,
            "content": content,
            "role": role,
            "display": display,
            "done": done,
        }
        if data:
            message["data"] = data
        record_message(**message)
        emit("response", message)

    for attempt in range(10):  # Number of attempts to ask the user for more information
        # Check if the user has stopped the query
        if conversation_stop_flags.get(conversation_id):
            return

        response = conversation.chat_gpt.ask(question)
        sql = extract_sql(response)

        if "DONE" in response:  # Check if the response contains "DONE"
            response = response.replace("DONE", "").strip()
            return emit_message(response, done=True)
        if not sql:
            return emit_message(response, done=False)
        else:
            # If the answer contains an SQL query, try to execute it
            emit_message(response, display=False)
            try:
                MAX_DATA_SIZE = 4000  # Maximum size of the data to return
                # Assuming you have a Database instance named 'database'
                results = datalake.query(sql)
            except Exception as e:
                # If there's an error executing the query, inform the user
                question = ERROR_TEMPLATE.format(error=str(e))
                emit_message(question, role="system", display=False)
            else:
                # Take every row until the total size is less than 1000 characters
                results_limited = []
                total_size = 0
                for row in results:
                    results_limited.append(row)
                    total_size += len(json.dumps(row, default=str))
                    if total_size > MAX_DATA_SIZE:
                        break

                # Display in JSON
                # TODO: switch to CSV (more economical)
                results_dumps = json.dumps(results_limited, default=str)
                if total_size > MAX_DATA_SIZE:
                    results_dumps += "\n..."

                # Send the result back to chat_gpt as the new question
                question = RESULT_TEMPLATE.format(
                    sample=results_dumps,
                    len_sample=len(results_limited),
                    len_total=len(results),
                )
                emit_message(
                    question, role="system", display=False, data=results_limited
                )
