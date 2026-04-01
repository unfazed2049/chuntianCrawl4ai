import tempfile
import unittest
import inspect
from pathlib import Path
from unittest.mock import patch

import meilisearch_tasks


class MeilisearchIndexInputTests(unittest.TestCase):
    def test_collect_json_sidecars_uses_explicit_paths(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            p1 = base / "a.json"
            p2 = base / "b.json"
            txt = base / "note.txt"
            p1.write_text("{}", encoding="utf-8")
            p2.write_text("{}", encoding="utf-8")
            txt.write_text("x", encoding="utf-8")

            files = meilisearch_tasks._collect_json_sidecars(
                workspace="any",
                date="20260101",
                json_paths=[
                    str(p1),
                    str(p2),
                    str(txt),
                    str(p1),
                    str(base / "missing.json"),
                ],
            )

            self.assertEqual(files, [p1, p2])

    def test_collect_json_sidecars_falls_back_to_scan_root(self):
        with tempfile.TemporaryDirectory() as td:
            output_root = Path(td)
            scan_root = output_root / "demo" / "20260101"
            scan_root.mkdir(parents=True, exist_ok=True)
            p1 = scan_root / "a.json"
            p2 = scan_root / "nested" / "b.json"
            p2.parent.mkdir(parents=True, exist_ok=True)
            p1.write_text("{}", encoding="utf-8")
            p2.write_text("{}", encoding="utf-8")

            with patch.object(meilisearch_tasks, "OUTPUT_ROOT", output_root):
                files = meilisearch_tasks._collect_json_sidecars(
                    workspace="demo", date="20260101", json_paths=None
                )

            self.assertEqual(set(files), {p1, p2})

    def test_pre_index_filter_defaults_keep_when_prompt_missing(self):
        keep, reason = meilisearch_tasks.pre_index_filter_task.fn(
            llm_cfg={},
            prompts={},
            meta={"url": "https://example.com"},
            cleaned_content="hello",
        )
        self.assertTrue(keep)
        self.assertIn("未配置", reason)

    def test_pre_index_filter_uses_llm_result(self):
        with patch.object(
            meilisearch_tasks,
            "call_llm",
            return_value={"keep": False, "reason": "广告页"},
        ):
            keep, reason = meilisearch_tasks.pre_index_filter_task.fn(
                llm_cfg={"provider": "x", "api_token": "y"},
                prompts={"index_pre_filter": {"instruction": "filter"}},
                meta={"url": "https://example.com"},
                cleaned_content="hello",
            )

        self.assertFalse(keep)
        self.assertEqual(reason, "广告页")

    def test_index_tasks_accept_raw_content_only(self):
        for task_obj in (
            meilisearch_tasks.index_competitor_news_task,
            meilisearch_tasks.index_industry_news_task,
            meilisearch_tasks.index_trade_show_task,
        ):
            params = inspect.signature(task_obj.fn).parameters
            self.assertIn("raw_content", params)
            self.assertNotIn("cleaned_content", params)


if __name__ == "__main__":
    unittest.main()
