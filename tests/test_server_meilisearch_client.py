import unittest
from unittest.mock import patch

from meilisearch.errors import MeilisearchApiError
from requests import Response

import server.utils.meilisearch_client as meili_client


class _FakeIndex:
    def __init__(self, error: Exception | list[Exception | None] | None = None):
        self._error = error
        self.search_calls = []
        self.settings_calls = []
        self.settings_applied = False

    def search(self, query: str, options: dict):
        self.search_calls.append((query, options))
        if self._error == "needs_settings" and not self.settings_applied:
            raise _build_meili_api_error(
                400,
                '{"message":"Index `trade_shows`: Attribute `workspace` is not filterable.","code":"invalid_search_filter"}',
            )
        if self._error == "needs_settings" and self.settings_applied:
            error = None
        else:
            error = self._error

        if isinstance(error, list):
            error = error.pop(0) if error else None

        if error is None:
            return {
                "hits": [],
                "estimatedTotalHits": 0,
                "limit": options.get("limit", 20),
                "offset": options.get("offset", 0),
                "processingTimeMs": 0,
            }
        raise error

    def update_settings(self, payload: dict):
        self.settings_calls.append(payload)
        return {"taskUid": 123}


class _FakeClient:
    def __init__(self, error: Exception | list[Exception | None] | None = None):
        self._error = error
        self.indexes: dict[str, _FakeIndex] = {}

    def index(self, uid: str):
        if uid not in self.indexes:
            self.indexes[uid] = _FakeIndex(self._error)
        return self.indexes[uid]

    def wait_for_task(self, task_uid: int, timeout_in_ms: int = 5000):
        for index in self.indexes.values():
            index.settings_applied = True
        return {"taskUid": task_uid, "status": "succeeded"}


def _build_meili_api_error(status_code: int, body_json: str) -> MeilisearchApiError:
    response = Response()
    response.status_code = status_code
    response._content = body_json.encode("utf-8")
    return MeilisearchApiError("meili error", response)


class HybridSearchRobustnessTests(unittest.IsolatedAsyncioTestCase):
    async def test_returns_empty_result_when_index_not_found(self):
        err = _build_meili_api_error(
            404,
            '{"message":"Index `competitor_profiles` not found.","code":"index_not_found"}',
        )

        with patch.object(
            meili_client, "get_meilisearch_client", return_value=_FakeClient(err)
        ):
            result = await meili_client.hybrid_search(
                index_name="competitor_profiles",
                query="",
                workspace="default",
                limit=100,
                offset=0,
                semantic_ratio=0.4,
            )

        self.assertEqual(result["hits"], [])
        self.assertEqual(result["estimatedTotalHits"], 0)
        self.assertEqual(result["limit"], 100)
        self.assertEqual(result["offset"], 0)

    async def test_combines_workspace_and_filter_expression(self):
        client = _FakeClient()

        with patch.object(meili_client, "get_meilisearch_client", return_value=client):
            await meili_client.hybrid_search(
                index_name="competitor_news",
                query="",
                workspace="hpp",
                limit=50,
                offset=0,
                semantic_ratio=0.4,
                filter_expr='competitor_id = "acme"',
            )

        _, options = client.index("competitor_news").search_calls[0]
        self.assertEqual(
            options["filter"], 'workspace = "hpp" AND competitor_id = "acme"'
        )

    async def test_repairs_filterable_attributes_and_retries_once(self):
        err = _build_meili_api_error(
            400,
            '{"message":"Index `industry_news`: Attribute `workspace` is not filterable.","code":"invalid_search_filter"}',
        )
        client = _FakeClient([err, None])

        with patch.object(meili_client, "get_meilisearch_client", return_value=client):
            result = await meili_client.hybrid_search(
                index_name="industry_news",
                query="",
                workspace="hpp",
                limit=20,
                offset=0,
                semantic_ratio=0.4,
            )

        index = client.index("industry_news")
        self.assertEqual(len(index.search_calls), 2)
        self.assertEqual(
            index.settings_calls[0]["filterableAttributes"], ["workspace", "category"]
        )
        self.assertEqual(result["hits"], [])

    async def test_waits_for_settings_task_before_retrying(self):
        client = _FakeClient("needs_settings")

        with patch.object(meili_client, "get_meilisearch_client", return_value=client):
            result = await meili_client.hybrid_search(
                index_name="trade_shows",
                query="",
                workspace="hpp",
                limit=20,
                offset=0,
                semantic_ratio=0.4,
            )

        index = client.index("trade_shows")
        self.assertEqual(len(index.search_calls), 2)
        self.assertTrue(index.settings_applied)
        self.assertEqual(result["hits"], [])


class MeilisearchBootstrapSettingsTests(unittest.TestCase):
    def test_ensure_filterable_attributes_for_known_indexes_updates_all(self):
        client = _FakeClient()

        with patch.object(meili_client, "get_meilisearch_client", return_value=client):
            meili_client.ensure_filterable_attributes_for_known_indexes()

        for index_name in meili_client.FILTERABLE_ATTRIBUTES_BY_INDEX:
            index = client.index(index_name)
            self.assertEqual(len(index.settings_calls), 1)
            self.assertEqual(
                index.settings_calls[0]["filterableAttributes"],
                meili_client.FILTERABLE_ATTRIBUTES_BY_INDEX[index_name],
            )


if __name__ == "__main__":
    unittest.main()
