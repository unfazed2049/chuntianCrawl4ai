import json
import tempfile
import unittest
from pathlib import Path

from prefect_tasks import save_json_task


class PrefectSaveJsonTests(unittest.TestCase):
    def test_save_json_keeps_only_meta_and_raw_content(self):
        with tempfile.TemporaryDirectory() as td:
            output_dir = Path(td)
            out = save_json_task.fn(
                output_dir=output_dir,
                slug="page",
                extracted={},
                raw_content="Home | About\n\nMain paragraph\n\n![img](https://a.com/1.png)",
                meta={"url": "https://example.com"},
            )

            payload = json.loads(Path(out).read_text(encoding="utf-8"))
            self.assertEqual(set(payload.keys()), {"meta", "raw_content"})
            self.assertIn("raw_content", payload)
            self.assertEqual(payload["meta"], {"url": "https://example.com"})


if __name__ == "__main__":
    unittest.main()
