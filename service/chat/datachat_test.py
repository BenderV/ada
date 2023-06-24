import os
import unittest
from unittest.mock import MagicMock, patch

from back.models import Conversation, ConversationMessage
from back.session import session
from chat import datachat
from chat.chatgpt import ChatGPT
from chat.lock import StopException
from chat.utils import find_closest_embeddings

# class TestDatabaseChat(unittest.TestCase):
#     def setUp(self):
#         self.database_id = 0
#         self.conversation_id = 0
#         self.stop_flags = {}

#     def test_done(self):
#         with patch(
#             "chat.datachat.DatabaseChat.chat_gpt", new_callable=MagicMock
#         ) as mock_chat_gpt:
#             mock_chat_gpt.ask.return_value = "Test message DONE"

#             chat = datachat.DatabaseChat(
#                 self.database_id,
#                 conversation_id=self.conversation_id,
#                 stop_flags=self.stop_flags,
#             )

#             result = list(chat.ask("Test question"))

#             mock_chat_gpt.ask.assert_called_once()

#             # Delete the conversations from the database
#             session.query(ConversationMessage).filter_by(conversationId=0).delete(),
#             session.commit()

#     def test_memory(self):
#         with patch(
#             "chat.datachat.DatabaseChat.chat_gpt", new_callable=MagicMock
#         ) as mock_chat_gpt:
#             mock_chat_gpt.ask.side_effect = [
#                 "MEMORY_SEARCH(test)",
#                 "SELECT * FROM test",
#                 "DONE",
#             ]

#             chat = datachat.DatabaseChat(
#                 self.database_id,
#                 conversation_id=self.conversation_id,
#                 stop_flags=self.stop_flags,
#             )

#             list(chat.ask("Test question"))

#             # # Delete the conversations from the database
#             # session.query(ConversationMessage).filter_by(conversationId=0).delete(),
#             # session.commit()


class TestDatabaseChat(unittest.TestCase):
    def test_find_closest_embeddings(self):
        query = "Number of circuits per country"
        closest_queries = find_closest_embeddings(query, top_n=2)
        print(closest_queries)
        for q in closest_queries:
            print(q.query)

        assert closest_queries[0].query == "Show number of races per country"
        assert (
            closest_queries[1].query
            == "For each circuits, give the year there was the fist race organised"
        )


if __name__ == "__main__":
    unittest.main()
