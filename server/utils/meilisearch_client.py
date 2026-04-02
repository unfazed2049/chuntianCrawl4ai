"""
Meilisearch 客户端封装
"""

from meilisearch import Client
from meilisearch.errors import MeilisearchApiError
from server.config import MEILISEARCH_CONFIG
from typing import Any, Optional


FILTERABLE_ATTRIBUTES_BY_INDEX: dict[str, list[str]] = {
    "industry_news": ["workspace", "category"],
    "competitor_news": [
        "workspace",
        "competitor_id",
        "competitor_name",
        "source_section",
    ],
    "trade_shows": ["workspace", "year", "month", "name"],
    "competitor_profiles": ["workspace", "competitor_id", "country", "name"],
}


class MeilisearchClient:
    """Meilisearch 客户端单例"""

    _instance: Optional[Client] = None

    @classmethod
    def get_client(cls) -> Client:
        """获取 Meilisearch 客户端实例"""
        if cls._instance is None:
            cls._instance = Client(
                MEILISEARCH_CONFIG["url"], MEILISEARCH_CONFIG["api_key"]
            )
        return cls._instance


def get_meilisearch_client() -> Client:
    """依赖注入函数"""
    return MeilisearchClient.get_client()


def _wait_for_settings_task(client: Any, task_result: Any) -> None:
    task_uid = None
    if isinstance(task_result, dict):
        task_uid = task_result.get("taskUid") or task_result.get("uid")

    if task_uid is not None and hasattr(client, "wait_for_task"):
        client.wait_for_task(task_uid, timeout_in_ms=5000)


def _repair_filterable_attributes(client: Any, index_name: str, index: Any) -> bool:
    filterable_attributes = FILTERABLE_ATTRIBUTES_BY_INDEX.get(index_name)
    if not filterable_attributes:
        return False

    task_result = index.update_settings({"filterableAttributes": filterable_attributes})
    _wait_for_settings_task(client, task_result)
    return True


def _is_invalid_filter_error(error: MeilisearchApiError) -> bool:
    error_text = str(error)
    return error.status_code == 400 and (
        "invalid_search_filter" in error_text or "not filterable" in error_text
    )


def ensure_filterable_attributes_for_known_indexes() -> None:
    client = get_meilisearch_client()

    for index_name, filterable_attributes in FILTERABLE_ATTRIBUTES_BY_INDEX.items():
        try:
            index = client.index(index_name)
            task_result = index.update_settings(
                {"filterableAttributes": filterable_attributes}
            )
            _wait_for_settings_task(client, task_result)
        except MeilisearchApiError as error:
            if error.status_code == 404:
                continue
            raise


async def hybrid_search(
    index_name: str,
    query: str = "",
    workspace: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    semantic_ratio: float = 0.4,
    filter_expr: Optional[str] = None,
) -> dict[str, Any]:
    """
    执行混合搜索

    Args:
        index_name: 索引名称
        query: 搜索查询
        workspace: 工作空间过滤
        limit: 返回数量限制
        offset: 偏移量
        semantic_ratio: 语义搜索比例 (0-1)
        filter_expr: 自定义过滤表达式

    Returns:
        搜索结果
    """
    client = get_meilisearch_client()
    index = client.index(index_name)

    # 构建搜索参数
    search_params: dict[str, Any] = {
        "limit": limit,
        "offset": offset,
    }

    # 添加过滤条件
    filters = []
    if workspace:
        filters.append(f'workspace = "{workspace}"')
    if filter_expr:
        filters.append(filter_expr)

    if filters:
        search_params["filter"] = " AND ".join(filters)

    # 如果启用混合搜索
    hybrid_config = MEILISEARCH_CONFIG.get("hybrid_search")
    if hybrid_config and hybrid_config.get("enabled"):
        search_params["hybrid"] = {
            "embedder": hybrid_config["embedder_name"],
            "semanticRatio": semantic_ratio,
        }

    # 执行搜索
    try:
        result = index.search(query, search_params)
    except MeilisearchApiError as e:
        if e.status_code == 404:
            return {
                "hits": [],
                "estimatedTotalHits": 0,
                "limit": limit,
                "offset": offset,
                "processingTimeMs": 0,
            }

        if search_params.get("filter") and _is_invalid_filter_error(e):
            repaired = _repair_filterable_attributes(client, index_name, index)
            if repaired:
                result = index.search(query, search_params)
                return result

        raise
    return result
