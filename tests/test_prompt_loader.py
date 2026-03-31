import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import utils


class PromptLoaderTests(unittest.TestCase):
    def test_load_prompts_reads_markdown_only(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            prompts_dir = Path(temp_dir)
            (prompts_dir / "a.md").write_text("instruction a", encoding="utf-8")
            (prompts_dir / "b.json").write_text(
                '{"instruction": "instruction b"}', encoding="utf-8"
            )

            with patch.object(utils, "PROMPTS_DIR", prompts_dir):
                prompts = utils.load_prompts()

        self.assertIn("a", prompts)
        self.assertEqual(prompts["a"]["instruction"], "instruction a")
        self.assertNotIn("b", prompts)

    def test_crawler_reuses_utils_load_prompts(self):
        crawler_source = (Path(__file__).resolve().parents[1] / "crawler.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("from utils import load_prompts", crawler_source)
        self.assertNotIn("def load_prompts(", crawler_source)


if __name__ == "__main__":
    unittest.main()
