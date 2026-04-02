"""
搜索相关路由
"""

from fastapi import APIRouter, Query
from server.models.search import ApiResponse, SearchResult
from server.utils.meilisearch_client import hybrid_search

router = APIRouter()


@router.get("", response_model=ApiResponse[SearchResult])
async def search(
    index: str = Query(..., description="索引名称"),
    q: str = Query("", description="搜索查询"),
    workspace: str = Query("default", description="工作空间"),
    filter: str | None = Query(None, description="附加过滤条件"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    semantic_ratio: float = Query(0.4, ge=0.0, le=1.0, description="语义搜索比例"),
):
    """
    通用搜索接口

    支持的索引:
    - competitor_news: 竞争对手新闻
    - industry_news: 行业新闻
    - trade_shows: 展会信息
    - competitor_profiles: 竞争对手档案
    """
    result = await hybrid_search(
        index_name=index,
        query=q,
        workspace=workspace,
        filter_expr=filter,
        limit=limit,
        offset=offset,
        semantic_ratio=semantic_ratio,
    )

    search_result = SearchResult(
        hits=result["hits"],
        total=result["estimatedTotalHits"],
        limit=result["limit"],
        offset=result["offset"],
        processing_time_ms=result["processingTimeMs"],
    )

    return ApiResponse(
        success=True,
        data=search_result,
        message="搜索成功",
        total=search_result.total,
    )
