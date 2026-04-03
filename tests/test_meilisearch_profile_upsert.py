import sys
import types
import unittest
from unittest.mock import patch


if "litellm" not in sys.modules:
    litellm_mod = types.ModuleType("litellm")
    setattr(litellm_mod, "completion", lambda **_: None)
    sys.modules["litellm"] = litellm_mod

if "meilisearch" not in sys.modules:
    meili_mod = types.ModuleType("meilisearch")
    setattr(meili_mod, "Client", object)
    sys.modules["meilisearch"] = meili_mod

if "prefect" not in sys.modules:

    def _identity_decorator(*_args, **_kwargs):
        def _wrap(func):
            setattr(func, "fn", func)
            return func

        return _wrap

    prefect_mod = types.ModuleType("prefect")
    setattr(prefect_mod, "flow", _identity_decorator)
    setattr(prefect_mod, "task", _identity_decorator)
    sys.modules["prefect"] = prefect_mod

import meilisearch_tasks


class _FakeIndex:
    def __init__(self):
        self.docs = {}
        self.primary_keys = []

    def get_document(self, doc_id: str):
        if doc_id not in self.docs:
            raise RuntimeError("not found")
        return self.docs[doc_id]

    def update_documents(self, docs: list[dict], primary_key: str | None = None):
        self.primary_keys.append(primary_key)
        for doc in docs:
            self.docs[doc["id"]] = doc
        return {"taskUid": 1}


class _FakeClient:
    def __init__(self, wait_result: dict | None = None):
        self._indexes = {"competitor_profiles": _FakeIndex()}
        self.wait_calls = []
        self.wait_result = wait_result or {"status": "succeeded"}

    def index(self, uid: str):
        return self._indexes[uid]

    def wait_for_task(self, task_uid: int, timeout_in_ms: int = 0):
        self.wait_calls.append((task_uid, timeout_in_ms))
        return self.wait_result


class MeilisearchProfileUpsertTests(unittest.TestCase):
    def test_wait_for_update_task_raises_when_meili_task_failed(self):
        client = _FakeClient(
            wait_result={
                "status": "failed",
                "error": {
                    "code": "index_primary_key_multiple_candidates_found",
                    "message": "multiple id candidates",
                },
            }
        )

        with self.assertRaises(RuntimeError):
            meilisearch_tasks._wait_for_update_task(client, {"taskUid": 99})

    def test_upsert_uses_fallback_when_llm_merge_fails(self):
        client = _FakeClient()
        prompts = {"index_competitor_profile": {"instruction": "merge"}}

        with patch.object(
            meilisearch_tasks, "call_llm", side_effect=RuntimeError("llm down")
        ):
            upsert_task = getattr(
                meilisearch_tasks.upsert_competitor_profile_task,
                "fn",
                meilisearch_tasks.upsert_competitor_profile_task,
            )
            upsert_task(
                client=client,
                llm_cfg={"provider": "x", "api_token": "y"},
                prompts=prompts,
                workspace="hpp",
                competitor_id="山西海普瑞科技有限公司",
                site_name="山西海普瑞科技有限公司",
                new_items=[
                    {
                        "data_type": "technologies",
                        "url": "https://example.com/a",
                        "raw_content": "foo",
                    }
                ],
            )

        doc = client.index("competitor_profiles").docs["hpp_山西海普瑞科技有限公司"]
        self.assertEqual(doc["competitor_id"], "山西海普瑞科技有限公司")
        self.assertEqual(doc["workspace"], "hpp")
        self.assertEqual(doc["name"], "山西海普瑞科技有限公司")
        self.assertEqual(len(doc["technologies"]), 1)
        self.assertEqual(doc["technologies"][0]["source_url"], "https://example.com/a")
        self.assertEqual(
            client.index("competitor_profiles").primary_keys[-1],
            "id",
        )
        self.assertTrue(client.wait_calls)


if __name__ == "__main__":
    unittest.main()
