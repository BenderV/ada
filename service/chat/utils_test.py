import unittest

from chat.memory_utils import find_closest_embeddings
from chat.utils import parse_function


class TestDatabaseChat(unittest.TestCase):
    # TODO: Add mock generate_embedding from chat.utils, used in find_closest_embeddings
    # Also mockup the database

    def test_find_closest_embeddings(self):
        query = "Number of circuits per country"
        # TODO: fix add session...
        closest_queries = find_closest_embeddings(query, top_n=2)
        assert closest_queries[0].query == "Show all the circuits in France"
        assert closest_queries[1].query == "Show me all the circuits in France"


class TestParseFunction(unittest.TestCase):
    # def test_no_arguments(self):
    #     text = """
    #     > FUNCTION()
    #     """
    #     result = parse_function(text)
    #     expected = {"name": "FUNCTION", "arguments": "{}"}
    #     self.assertEqual(result, expected)

    def test_single_argument(self):
        text = """
        > FUNCTION(name="single argument")
        """
        result = parse_function(text)
        expected = {"name": "FUNCTION", "arguments": '{"name": "single argument"}'}
        self.assertEqual(result, expected)

    def test_multiple_arguments(self):
        text = """
        > FUNCTION(name="argument1", another="argument2")
        """
        result = parse_function(text)
        expected = {
            "name": "FUNCTION",
            "arguments": '{"name": "argument1", "another": "argument2"}',
        }
        self.assertEqual(result, expected)

    def test_multiline_argument(self):
        text = """
        > FUNCTION(name="argument1", query=```SELECT column
        FROM table;
        ```)
        """
        result = parse_function(text)
        expected = {
            "name": "FUNCTION",
            "arguments": '{"name": "argument1", "query": "SELECT column\\nFROM table;"}',
        }
        self.assertEqual(result, expected)

    def test_multiline_with_other_arguments(self):
        text = """
        > FUNCTION(name="argument1", description="describes something", query=```SELECT column
        FROM table;
        ```)
        """
        result = parse_function(text)
        expected = {
            "name": "FUNCTION",
            "arguments": '{"name": "argument1", "description": "describes something", "query": "SELECT column\\nFROM table;"}',
        }
        self.assertEqual(result, expected)

    def test_parse_function(self):
        text = """
        > SQL_QUERY(name="installation_date column examples", query=```SELECT installation_date
        FROM public.station
        ORDER BY RANDOM()
        LIMIT 5;
        ```)
        """
        result = parse_function(text)
        expected = {
            "name": "SQL_QUERY",
            "arguments": '{"name": "installation_date column examples", "query": "SELECT installation_date\\nFROM public.station\\nORDER BY RANDOM()\\nLIMIT 5;"}',
        }
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
