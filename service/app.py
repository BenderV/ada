import json
import os
import re

import openai
from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit

from chat import ChatGPT, parse_chat_template
from database import Database

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

instruction, examples = parse_chat_template("chat_template.txt")
chat_gpt = ChatGPT(instruction=instruction, examples=examples)

# Set your OpenAI API key
openai.api_key = os.environ["OPENAI_API_KEY"]

# Connect to your database
db_uri = "postgresql://postgres:postgres@localhost:5432/formula1"
database = Database(db_uri)


@app.route("/databases", methods=["GET"])
def get_databases():
    # Get database uri from request X-Database-URI header
    # db_uri = request.headers.get("X-Database-URI")
    return jsonify([database.name])


@app.route("/tables", methods=["GET"])
def get_tables():
    tables = [{"schema": t._schema, "table": t._table} for t in database.tables]
    return jsonify(tables)


# @socketio.on("ask")
# def handle_ask(question):
#     print("ask:", question)
#     response = chat_gpt.ask(question)
#     emit("response", response)


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


@socketio.on("ask")
def handle_ask(question, state=None):
    print("ask:", question, state)
    if state == 0:
        chat_gpt.reset()  # Reset the chatbot's memory

    question = f'In database "formula1"; {question}'

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
                result = database.query(sql)
                # Display in JSON
                result = json.dumps(result)
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


@app.route("/query", methods=["POST"])
def query_database():
    nl_query = request.json.get("query", "")

    if not nl_query:
        return jsonify({"error": "No query provided"}), 400

    prompt = f"Translate the following English query into SQL: {nl_query}"

    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        max_tokens=100,
        n=1,
        stop=None,
        temperature=0.5,
    )

    sql_query = response.choices[0].text.strip()
    try:
        result = database.query(sql_query)
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    socketio.run(app, debug=True)
