import json

from chat.chat import ChatGPT, parse_chat_template
from flask import Blueprint, g
from flask_socketio import emit
from middleware import user_middleware

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


def emit_message(content, sender="assistant", display=True, done=False):
    message = {"content": content, "sender": sender, "display": display, "done": done}
    emit("response", message)


# @user_middleware
@socketio.on("ask")
def handle_ask(question, state=None):
    print("ask:", question, state)
    if state == 0:
        chat_gpt.reset()  # Reset the chatbot's memory

    question = f"In Snowflake database; {question}"

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
                result = g.datalake.query(sql)
                # Display in JSON (only the first 20 rows)
                if len(result) > 10:
                    result = json.dumps(result[:10], default=str) + "\n..."

                # Send the result back to chat_gpt as the new question
                question = f"""
                    Here is the result of the SQL query:
                    ```json
                    {result}
                    ```
                """
                emit_message(question, sender="system", display=False)
            except Exception as e:
                # If there's an error executing the query, inform the user
                question = f"""An error occurred while executing the SQL query: 
                ```error
                {e}
                ```Please provide more information."""
                emit_message(question, sender="system", display=False)
