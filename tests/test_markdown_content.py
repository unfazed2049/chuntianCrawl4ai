import unittest

from markdown_utils import pick_markdown_content


class MarkdownContentTests(unittest.TestCase):
    def test_prefers_raw_markdown_to_preserve_images(self):
        class Obj:
            raw_markdown = "text\n\n![img](https://a.com/1.png)"
            fit_markdown = "text"

        self.assertEqual(
            pick_markdown_content(Obj()),
            "text\n\n![img](https://a.com/1.png)",
        )

    def test_fallback_to_fit_markdown_when_raw_missing(self):
        class Obj:
            raw_markdown = ""
            fit_markdown = "paragraph one\n\nparagraph two"

        self.assertEqual(pick_markdown_content(Obj()), "paragraph one\n\nparagraph two")


if __name__ == "__main__":
    unittest.main()
