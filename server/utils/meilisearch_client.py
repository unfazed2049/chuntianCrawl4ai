"""
Meilisearch 客户端封装
"""

from meilisearch import Client
from server.config import MEILISEARCH_CONFIG
from typing import Any, Optional


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
    result = index.search(query, search_params)
    return result
