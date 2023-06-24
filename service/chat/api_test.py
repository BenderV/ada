import unittest

from chat.api import extract_sql

double_sql = """
Apologies for the confusion earlier. I'll run two queries below to count the number of distinct attributes in both SAP (AIH) and PIM.

```sql
SELECT COUNT(DISTINCT crc) AS sap_attributes
FROM aih_crc;
```

```sql
SELECT COUNT(DISTINCT id) AS pim_attributes
FROM pim_attribut;
```
"""


class TestExtractSQL(unittest.TestCase):
    def test_single_sql_block(self):
        text = "Some text here\n```sql\nSELECT * FROM users;\n```\nMore text here"
        expected_output = ["SELECT * FROM users;"]
        self.assertEqual(extract_sql(text), expected_output)

    def test_multiple_sql_blocks(self):
        text = "Text\n```sql\nSELECT * FROM users;\n```\nText\n```sql\nINSERT INTO users VALUES (1, 'John');\n```"
        expected_output = [
            "SELECT * FROM users;",
            "INSERT INTO users VALUES (1, 'John');",
        ]
        self.assertEqual(extract_sql(text), expected_output)

    def test_no_sql_block(self):
        text = "Some text without any SQL blocks."
        expected_output = []
        self.assertEqual(extract_sql(text), expected_output)

    def test_mixed_code_blocks(self):
        text = "Text\n```sql\nSELECT * FROM users;\n```\nText\n```python\nprint('Hello, World!')\n```"
        expected_output = ["SELECT * FROM users;"]
        self.assertEqual(extract_sql(text), expected_output)

    def test_two_sql_blocks(self):
        expected_output = [
            "SELECT COUNT(DISTINCT crc) AS sap_attributes\nFROM aih_crc;",
            "SELECT COUNT(DISTINCT id) AS pim_attributes\nFROM pim_attribut;",
        ]
        self.assertEqual(extract_sql(double_sql), expected_output)


if __name__ == "__main__":
    unittest.main()
