import os
import tempfile
import unittest
from pathlib import Path

from app_config import load_app_config


class AppConfigTests(unittest.TestCase):
    def setUp(self):
        self.original_env = os.environ.copy()
        for key in list(os.environ.keys()):
            if key.startswith(("LLM_", "REDIS_", "MEILI_")):
                os.environ.pop(key, None)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_loads_llm_and_redis_from_env_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text(
                "\n".join(
                    [
                        "LLM_PROVIDER=gpt-4o-mini",
                        "LLM_API_TOKEN=sk-test",
                        "LLM_BASE_URL=https://fastcn.poloapi.com/v1",
                        "REDIS_BLOOM_ENABLED=true",
                        "REDIS_HOST=127.0.0.1",
                        "REDIS_PORT=6380",
                        "REDIS_DB=1",
                        "REDIS_BLOOM_KEY_PREFIX=crawl:detail",
                        "REDIS_BLOOM_ERROR_RATE=0.002",
                        "REDIS_BLOOM_CAPACITY=200000",
                        "MEILI_URL=http://localhost:7700",
                        "MEILI_API_KEY=master-key",
                    ]
                ),
                encoding="utf-8",
            )

            cfg = load_app_config(env_file=str(env_path))

            self.assertEqual(cfg["llm_config"]["provider"], "gpt-4o-mini")
            self.assertEqual(cfg["llm_config"]["api_token"], "sk-test")
            self.assertEqual(
                cfg["llm_config"]["base_url"], "https://fastcn.poloapi.com/v1"
            )
            self.assertTrue(cfg["redis_bloom_config"]["enabled"])
            self.assertEqual(cfg["redis_bloom_config"]["port"], 6380)
            self.assertEqual(cfg["redis_bloom_config"]["capacity"], 200000)
            self.assertEqual(cfg["meilisearch_config"]["url"], "http://localhost:7700")
            self.assertEqual(cfg["meilisearch_config"]["api_key"], "master-key")

    def test_missing_llm_provider_raises(self):
        os.environ["LLM_API_TOKEN"] = "sk-only-token"
        with self.assertRaises(ValueError):
            load_app_config(skip_dotenv=True)

    def test_hybrid_document_template_defaults_to_cleaned_content(self):
        os.environ["LLM_PROVIDER"] = "gpt-4o-mini"
        os.environ["LLM_API_TOKEN"] = "sk-test"
        os.environ["MEILI_HYBRID_ENABLED"] = "true"

        cfg = load_app_config(skip_dotenv=True)
        self.assertEqual(
            cfg["meilisearch_config"]["hybrid_search"]["document_template"],
            "{{doc.title}}\n{{doc.summary}}\n{{doc.cleaned_content}}",
        )


if __name__ == "__main__":
    unittest.main()
