import tempfile
import unittest
from pathlib import Path

import reindex_json_dir


class ReindexJsonDirTests(unittest.TestCase):
    def test_collect_json_paths_recursive(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            (base / "a.json").write_text("{}", encoding="utf-8")
            nested = base / "nested"
            nested.mkdir(parents=True, exist_ok=True)
            (nested / "b.json").write_text("{}", encoding="utf-8")
            (nested / "note.txt").write_text("x", encoding="utf-8")

            paths = reindex_json_dir.collect_json_paths(base, recursive=True)

            self.assertEqual(len(paths), 2)
            self.assertTrue(paths[0].endswith("a.json"))
            self.assertTrue(paths[1].endswith("b.json"))

    def test_collect_json_paths_non_recursive(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            (base / "a.json").write_text("{}", encoding="utf-8")
            nested = base / "nested"
            nested.mkdir(parents=True, exist_ok=True)
            (nested / "b.json").write_text("{}", encoding="utf-8")

            paths = reindex_json_dir.collect_json_paths(base, recursive=False)

            self.assertEqual(len(paths), 1)
            self.assertTrue(paths[0].endswith("a.json"))


if __name__ == "__main__":
    unittest.main()
