import unittest
from unittest.mock import patch

from meilisearch.errors import MeilisearchApiError
from requests import Response

import server.utils.meilisearch_client as meili_client


class _FakeIndex:
    def __init__(self, error: Exception):
        self._error = error

    def search(self, query: str, options: dict):
        raise self._error


class _FakeClient:
    def __init__(self, error: Exception):
        self._error = error

    def index(self, uid: str):
        return _FakeIndex(self._error)


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


if __name__ == "__main__":
    unittest.main()
