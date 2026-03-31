import unittest

from schemas import CRAWL_CONTENT_SCHEMA


class SchemaRegistryTests(unittest.TestCase):
    def test_crawl_schema_contains_only_content_fields(self):
        expected = {"title", "date", "content_markdown", "images"}
        self.assertEqual(set(CRAWL_CONTENT_SCHEMA.keys()), expected)
        self.assertNotIn("summary", CRAWL_CONTENT_SCHEMA)
        self.assertNotIn("tags", CRAWL_CONTENT_SCHEMA)


if __name__ == "__main__":
    unittest.main()
