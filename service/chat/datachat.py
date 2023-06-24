import copy
import re

from back.datalake import DatalakeFactory
from back.models import Conversation, ConversationMessage, Query
from back.session import session
from chat.chatgpt import ChatGPT, parse_chat_template
from chat.lock import StopException
from chat.sql_utils import extract_sql, run_sql
from chat.utils import message_replace_json_block_to_csv

MAX_DATA_SIZE = 4000  # Maximum size of the data to return
CONVERSATION_MAX_ATTEMPT = 10  # Number of exchange the AI can do before giving up


def format_message(**kwargs):
    # change lower_case keys to camelCase keys
    def camel_case(snake_str):
        components = snake_str.split("_")
        return components[0] + "".join(x.title() for x in components[1:])

    kwargs = {camel_case(k): v for k, v in kwargs.items()}
    return kwargs


def extract_memory_query(content):
    """
    >>> extract_memory_query("MEMORY_SEARCH(station)")
    'station'

    >>> extract_memory_query("blabla bla")
    """
    search = re.search(r'MEMORY_SEARCH\("?(.*)"?\)', content)
    if search:
        memory = search.group(1)
        return memory


def save_query(sql_query, message):
    return
    query = Query(
        query="???",
        # databaseId=message.databaseId,
        validatedSQL=sql_query,
        # messageId=message.id,
    )
    session.add(query)
    session.commit()


response = """
Previous queries:

{% for query in queries %}
>>> Query: Show pits stop duration distribution for year 2020
```sql
{{SQL}}
```
{% endfor %}
"""


class DatabaseChat:
    """
    ChatGPT with a database
    Intercept the exchange so if there is SQL in the conversion, it's executed,
    and the result is sent back to the AI. (unless there is "DONE" in the response)
    If there is a MEMORY_SEARCH() query, we intercept end send back proximate queries
    """

    def __init__(self, database_id, conversation_id=None, stop_flags=None):
        if conversation_id is None:
            # Create conversation object
            self.conversation = self._create_conversation(databaseId=database_id)
        else:
            self.conversation = (
                session.query(Conversation).filter_by(id=conversation_id).first()
            )

        # Add a datalake object to the request
        self.datalake = DatalakeFactory.create(
            self.conversation.database.engine,
            **self.conversation.database.details,
        )
        self.stop_flags = stop_flags

    def _create_conversation(self, databaseId, name=None):
        # Create conversation object
        conversation = Conversation(
            databaseId=databaseId,
            ownerId="admin",
            name=name,
        )
        session.add(conversation)
        session.commit()
        return conversation

    def _record_message(self, content, role="assistant", display=True, done=False):
        self.query_stop_flag()
        message = {
            "conversation_id": self.conversation.id,
            "content": content,
            "role": role,
            "display": display,
            "done": done,
        }
        formated_message = format_message(**message)
        conversaion_message = ConversationMessage(**formated_message)

        # If this is the first message, we set the conversation as started
        # if not self.conversation.started:
        #     self.conversation.started = True

        session.add(conversaion_message)
        session.commit()
        return message

    def query_stop_flag(self):
        if self.stop_flags.get(str(self.conversation.id)):
            raise StopException("Query stopped by user")

    @property
    def chat_gpt(self):
        instruction, examples = parse_chat_template("chat/chat_template.txt")
        chat_gpt = ChatGPT(instruction=instruction, examples=examples)

        messages = self.conversation.messages
        # deep copy the messages (to avoid modifying the database object)
        # why it is this: 'message' object has no attribute 'copy'
        messages = [copy.deepcopy(message) for message in messages]
        messages[
            0
        ].content = (
            f"In {self.conversation.database.engine} database, {messages[0].content}"
        )

        for message in messages:
            message.content = message_replace_json_block_to_csv(message.content)
        chat_gpt.load_history(messages)
        return chat_gpt

    # def ask_chat_gpt(self):
    #     return self.chat_gpt.ask()

    def ask(self, question):
        self._record_message(question, role="user")
        if not self.conversation.name:
            self.conversation.name = question

        for attempt in range(CONVERSATION_MAX_ATTEMPT):
            print(self.stop_flags, self.conversation.id)
            # Check if the user has stopped the query
            self.query_stop_flag()

            response = self.chat_gpt.ask()

            # Check if the response contains "DONE"
            if "DONE" in response:
                response = response.replace("DONE", "").strip()
                message = self._record_message(response, done=True)
                yield message
                return message

            sql_queries = extract_sql(response)
            memory_query = extract_memory_query(response)
            has_query = bool(sql_queries or memory_query)

            print(response, "memory_query", memory_query)

            if not has_query:
                """
                If the answer does not contain an query (SQL, Memory), we assume it's either:
                - The final answer
                - A question to the user
                """
                message = self._record_message(response, done=True)
                yield message
                return message
            else:
                # If the answer contains a query, try to execute it
                message = self._record_message(response, display=False)
                yield message

            if memory_query:
                # response = self.conversation.memory[memory]
                # Mock the response
                response = """
Previous queries:
    
>>> Query: Show pits stop duration distribution for year 2020
```sql
SELECT   round(pit_stops.milliseconds / 1000 ,2)
        ,COUNT(*) AS freq
FROM    pit_stops
JOIN    races
ON      races.raceid = pit_stops.raceid
WHERE  races.year = '2020'
GROUP BY  1
ORDER BY  1
```


>>> Query: Show number of races per country
```sql
SELECT circuits.country, COUNT(*)
FROM races
JOIN circuits ON (circuits.circuitid = races.circuitid)
GROUP BY 1
ORDER BY 2 DESC
```
"""
                print("memory_query", response)
                message = self._record_message(response, role="system", display=False)
                yield message

            if sql_queries:
                for sql_query in sql_queries:
                    save_query(sql_query, message)

                results = [run_sql(self.datalake, sql) for sql in sql_queries]

                if len(results) == 1:
                    response, _ = results[0]
                else:
                    # Join the results in a single string
                    response = "".join(
                        [
                            f"For the query number {i}:\n{message}"
                            for i, (message, _) in enumerate(results, start=1)
                        ]
                    )
                message = self._record_message(response, role="system", display=False)
                yield message

    def regenerate_last_message(self):
        # Delete the last message and reask the question
        last_message = self.conversation.messages[-1]
        session.delete(last_message)
        session.commit()
        yield from self.ask(last_message.content)
