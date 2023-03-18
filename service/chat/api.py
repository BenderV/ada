import json

from back.datalake import DatalakeFactory
from back.models import Conversation, ConversationMessage, Database
from back.session import session
from chat.chat import ChatGPT, parse_chat_template
from flask import Blueprint
from flask_socketio import emit

instruction, examples = parse_chat_template("chat/chat_template.txt")
chat_gpt = ChatGPT(instruction=instruction, examples=examples)

api = Blueprint("chat_api", __name__)

# socketio = SocketIO(cors_allowed_origins="*")
from app import socketio


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


RESULT_TEMPLATE = """Here is the result of the SQL query:
```json
{result}
```
"""

ERROR_TEMPLATE = """An error occurred while executing the SQL query:
```error
{error}
```
Please correct the query and try again.
"""


@socketio.on("ask")
def handle_ask(question, conversation_id=None):
    # formula1
    database = session.query(Database).filter_by(id=131).first()
    # Add a datalake object to the request
    datalake = DatalakeFactory.create(
        database.engine,
        **database.details,
    )

    print("ask:", question, conversation_id)
    if not conversation_id:
        """
        id = Column(Integer, primary_key=True)
        name = Column(String, nullable=False)
        ownerId = Column(String, ForeignKey("user.id"))
        createdAt = Column(TIMESTAMP, nullable=False, default=text("now()"))
        updatedAt = Column(TIMESTAMP, nullable=False, default=text("now()"))

        """
        # Create conversation object
        conversation = create_conversation(
            name=question, databaseId=database.id, ownerId="admin"
        )
        conversation_id = conversation.id
        # Reset the chatbot's memory
        chat_gpt.reset()  # Reset the chatbot's memory
        question = f"In {datalake.engine.dialect.name} database; {question}"

    user_question = {
        "conversation_id": conversation_id,
        "content": question,
        "role": "user",
        "display": True,
        "done": False,
    }
    record_message(**user_question)

    def emit_message(content, role="assistant", display=True, done=False, data=None):
        # TODO: record more stuff

        message = {
            "conversation_id": conversation_id,
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
        response = chat_gpt.ask(question)
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
                # Assuming you have a Database instance named 'database'
                results = datalake.query(sql)
                # Display in JSON (only the first 20 rows)
                results_limited = results[:10]
                results_dumps = json.dumps(results_limited, default=str)
                if len(results) > 10:
                    results_dumps += "\n..."

                # Send the result back to chat_gpt as the new question
                question = RESULT_TEMPLATE.format(result=results_dumps)
                emit_message(
                    question, role="system", display=False, data=results_limited
                )
            except Exception as e:
                # If there's an error executing the query, inform the user
                question = ERROR_TEMPLATE.format(error=str(e))

                emit_message(question, role="system", display=False)
