from back.datalake import DatalakeFactory
from back.models import Conversation, ConversationMessage
from back.session import session
from chat.chat import ChatGPT, parse_chat_template
from chat.lock import StopException
from chat.sql_utils import extract_sql, run_sql

MAX_DATA_SIZE = 4000  # Maximum size of the data to return
CONVERSATION_MAX_ATTEMPT = 10  # Number of exchange the AI can do before giving up


def format_message(**kwargs):
    # change lower_case keys to camelCase keys
    def camel_case(snake_str):
        components = snake_str.split("_")
        return components[0] + "".join(x.title() for x in components[1:])

    kwargs = {camel_case(k): v for k, v in kwargs.items()}
    return kwargs


class DatabaseChat:
    def __init__(self, database_id, conversation_id=None, stop_flags=None):
        if not conversation_id:
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
        if len(messages) == 1:
            messages[0].content = (
                # TODO: change this to a more generic message
                "In PostgreSQL database "
                + self.conversation.database.name
                + ", "
                + messages[0].content
            )
        chat_gpt.load_history(messages)
        return chat_gpt

    # def save_and_emit_message(
    #     self, content, role="assistant", display=True, done=False
    # ):
    #     # TODO
    #     message = {
    #         "content": content,
    #         "role": role,
    #         "display": display,
    #         "done": done,
    #     }
    #     self._record_message(**message)
    #     yield message

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

            if not sql_queries:
                """
                If the answer does not contain an SQL query, we assume it's either:
                - The final answer
                - A question to the user
                """
                message = self._record_message(response, done=True)
                yield message
                return message
            else:
                # If the answer contains an SQL query, try to execute it
                message = self._record_message(response, display=False)
                yield message

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
