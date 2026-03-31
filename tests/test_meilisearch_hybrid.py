import unittest

from meilisearch_settings import ensure_hybrid_settings
from search_service import hybrid_search


class FakeIndex:
    def __init__(self, uid: str):
        self.uid = uid
        self.settings_calls = []
        self.search_calls = []

    def update_settings(self, payload: dict):
        self.settings_calls.append(payload)

    def search(self, query: str, options: dict):
        self.search_calls.append((query, options))
        return {"hits": [], "index": self.uid}


class FakeClient:
    def __init__(self):
        self.indexes = {}

    def index(self, uid: str):
        if uid not in self.indexes:
            self.indexes[uid] = FakeIndex(uid)
        return self.indexes[uid]


class MeilisearchHybridTests(unittest.TestCase):
    def test_ensure_hybrid_settings_updates_embedders(self):
        client = FakeClient()
        embedder_name = "openai-emb"
        embedder_settings = {
            "source": "rest",
            "url": "https://api.openai.com/v1/embeddings",
            "dimensions": 1536,
            "headers": {
                "Authorization": "Bearer sk-test",
                "Content-Type": "application/json",
            },
            "request": {
                "model": "text-embedding-3-small",
                "input": ["{{text}}", "{{..}}"],
            },
            "response": {"data": [{"embedding": "{{embedding}}"}, "{{..}}"]},
        }

        ensure_hybrid_settings(
            client=client,
            index_uids=["industry_news", "competitor_news"],
            embedder_name=embedder_name,
            embedder_settings=embedder_settings,
            filterable_attrs=["workspace", "category"],
        )

        for index_uid in ["industry_news", "competitor_news"]:
            index = client.index(index_uid)
            self.assertEqual(len(index.settings_calls), 1)
            payload = index.settings_calls[0]
            self.assertIn("embedders", payload)
            self.assertIn(embedder_name, payload["embedders"])
            self.assertEqual(payload["embedders"][embedder_name]["source"], "rest")

    def test_hybrid_search_builds_expected_options(self):
        client = FakeClient()

        hybrid_search(
            client=client,
            index_uid="industry_news",
            query="超高压灭菌",
            embedder_name="openai-emb",
            semantic_ratio=0.4,
            limit=15,
            filter_expr='workspace = "default"',
        )

        index = client.index("industry_news")
        self.assertEqual(len(index.search_calls), 1)
        query, options = index.search_calls[0]
        self.assertEqual(query, "超高压灭菌")
        self.assertEqual(options["limit"], 15)
        self.assertEqual(options["hybrid"]["embedder"], "openai-emb")
        self.assertEqual(options["hybrid"]["semanticRatio"], 0.4)
        self.assertEqual(options["filter"], 'workspace = "default"')


if __name__ == "__main__":
    unittest.main()
