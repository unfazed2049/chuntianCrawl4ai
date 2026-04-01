import re
import unittest

from prefect_tasks import build_meta


class PrefectMetaTimeTests(unittest.TestCase):
    def test_build_meta_uses_asia_shanghai_offset(self):
        meta = build_meta(
            site={"name": "Demo Site", "competitor_id": "demo"},
            section={"name": "Demo Section", "data_type": "news"},
            workspace="default",
            url="https://example.com/page",
        )

        crawled_at = meta["crawled_at"]
        self.assertRegex(crawled_at, r"^\d{4}-\d{2}-\d{2}T")
        self.assertRegex(crawled_at, r"\+08:00$")


if __name__ == "__main__":
    unittest.main()
