import unittest

from utils import message_replace_json_block_to_csv


class TestMessageReplaceJsonBlockToCsv(unittest.TestCase):
    def test_single_json_block(self):
        input_content = 'Hello, here is some data: ```json\n[{"key": "value"}]\n```'
        expected_output = "Hello, here is some data: ```csv\nkey\nvalue\n```"

        output_content = message_replace_json_block_to_csv(input_content)
        self.assertEqual(output_content, expected_output)

    def test_multiple_json_blocks(self):
        input_content = (
            "Hello, here are multiple blocks:\n"
            'First: ```json\n[{"key1": "value1"}]\n```\n'
            'Second: ```json\n[{"key2": "value2"}]\n```'
        )
        expected_output = (
            "Hello, here are multiple blocks:\n"
            "First: ```csv\nkey1\nvalue1\n```\n"
            "Second: ```csv\nkey2\nvalue2\n```"
        )

        output_content = message_replace_json_block_to_csv(input_content)
        self.assertEqual(output_content, expected_output)

    def test_no_json_blocks(self):
        input_content = "Hello, there are no JSON blocks in this message."
        expected_output = "Hello, there are no JSON blocks in this message."

        output_content = message_replace_json_block_to_csv(input_content)
        self.assertEqual(output_content, expected_output)


if __name__ == "__main__":
    unittest.main()
