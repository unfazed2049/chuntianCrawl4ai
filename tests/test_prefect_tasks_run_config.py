import unittest

from prefect.cache_policies import NO_CACHE

from prefect_tasks import build_crawler_run_config
from prefect_tasks import (
    collect_urls_js_pagination_task,
    collect_urls_url_template_task,
    crawl_detail_pages_task,
    crawl_single_page_task,
)


class BuildCrawlerRunConfigTests(unittest.TestCase):
    def test_build_without_llm_strategy(self):
        cfg = build_crawler_run_config({"wait_for": "css:.list-item"})

        self.assertEqual(cfg.wait_for, "css:.list-item")
        self.assertIsNone(getattr(cfg, "extraction_strategy", None))


class TaskCachePolicyTests(unittest.TestCase):
    def test_crawler_tasks_use_no_cache_policy(self):
        tasks = [
            collect_urls_url_template_task,
            collect_urls_js_pagination_task,
            crawl_detail_pages_task,
            crawl_single_page_task,
        ]
        for task_obj in tasks:
            self.assertEqual(task_obj.cache_policy, NO_CACHE)


if __name__ == "__main__":
    unittest.main()
