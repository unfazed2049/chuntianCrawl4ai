import unittest

from markdown_utils import pick_markdown_content


class _MarkdownObj:
    def __init__(self, raw_markdown: str = "", fit_markdown: str = ""):
        self.raw_markdown = raw_markdown
        self.fit_markdown = fit_markdown


class PickMarkdownContentTests(unittest.TestCase):
    def test_prefers_raw_markdown(self):
        md = _MarkdownObj(raw_markdown="raw body", fit_markdown="fit body")
        self.assertEqual(pick_markdown_content(md), "raw body")

    def test_accepts_plain_markdown_string(self):
        self.assertEqual(pick_markdown_content("plain markdown"), "plain markdown")


if __name__ == "__main__":
    unittest.main()
