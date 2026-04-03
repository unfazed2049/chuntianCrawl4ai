import unittest
from unittest.mock import patch

import meilisearch_tasks


class FakeClient:
    def index(self, uid: str):
        class _Index:
            def update_settings(self, payload: dict):
                return payload

        return _Index()


class MeilisearchTaskHybridSettingsTests(unittest.TestCase):
    def test_uses_per_index_document_template_when_provided(self):
        meili_config = {
            "hybrid_search": {
                "enabled": True,
                "embedder_name": "openai-emb",
                "endpoint": "https://api.example.com/embeddings",
                "api_key": "sk-test",
                "model": "text-embedding-3-small",
                "dimensions": 1536,
                "indexes": ["industry_news", "trade_shows"],
                "document_template": "{{doc.title}}\n{{doc.summary}}",
                "document_templates": {
                    "trade_shows": "{{doc.name}}\n{{doc.summary}}",
                },
            }
        }

        with patch.object(meilisearch_tasks, "ensure_hybrid_settings") as mocked:
            meilisearch_tasks._ensure_hybrid_search_if_configured(
                client=FakeClient(),
                meili_config=meili_config,
            )

        self.assertEqual(mocked.call_count, 2)
        calls = mocked.call_args_list
        self.assertEqual(calls[0].kwargs["index_uids"], ["industry_news"])
        self.assertEqual(calls[1].kwargs["index_uids"], ["trade_shows"])
        self.assertEqual(
            calls[0].kwargs["embedder_settings"]["documentTemplate"],
            "{{doc.title}}\n{{doc.summary}}",
        )
        self.assertEqual(
            calls[1].kwargs["embedder_settings"]["documentTemplate"],
            "{{doc.name}}\n{{doc.summary}}",
        )


if __name__ == "__main__":
    unittest.main()
