import unittest

from markdown_cleaner import clean_markdown_content


class MarkdownCleanerTests(unittest.TestCase):
    def test_keeps_paragraphs_headings_lists_and_images(self):
        raw = """# Title

Welcome paragraph.

- item 1
- item 2

![hero](https://example.com/a.png)

Second paragraph.
"""
        cleaned = clean_markdown_content(raw)

        self.assertIn("# Title", cleaned)
        self.assertIn("Welcome paragraph.", cleaned)
        self.assertIn("- item 1", cleaned)
        self.assertIn("![hero](https://example.com/a.png)", cleaned)
        self.assertIn("\n\nSecond paragraph.", cleaned)

    def test_removes_common_navigation_noise(self):
        raw = """Home | About | Contact

Accept cookies

Main story paragraph.
"""
        cleaned = clean_markdown_content(raw)

        self.assertNotIn("Home | About | Contact", cleaned)
        self.assertNotIn("Accept cookies", cleaned)
        self.assertIn("Main story paragraph.", cleaned)


if __name__ == "__main__":
    unittest.main()
