"""
行业新闻相关路由
"""

from fastapi import APIRouter, Query
from server.models.search import ApiResponse
from server.models.news import IndustryNews
from server.utils.meilisearch_client import hybrid_search

router = APIRouter()


@router.get("", response_model=ApiResponse[list[IndustryNews]])
async def get_industry_news(
    workspace: str = Query("default", description="工作空间"),
    category: str = Query(None, description="新闻分类"),
    q: str = Query("", description="搜索查询"),
    limit: int = Query(50, ge=1, le=200, description="返回数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    semantic_ratio: float = Query(0.4, ge=0.0, le=1.0, description="语义搜索比例"),
):
    """获取行业新闻列表"""
    filter_expr = None
    if category:
        filter_expr = f'category = "{category}"'

    result = await hybrid_search(
        index_name="industry_news",
        query=q,
        workspace=workspace,
        filter_expr=filter_expr,
        limit=limit,
        offset=offset,
        semantic_ratio=semantic_ratio,
    )

    return ApiResponse(
        success=True,
        data=result["hits"],
        message="获取成功",
        total=result["estimatedTotalHits"],
    )


@router.get("/categories", response_model=ApiResponse[list[str]])
async def get_news_categories(
    workspace: str = Query("default", description="工作空间"),
):
    """获取新闻分类列表"""
    # 获取所有新闻
    result = await hybrid_search(
        index_name="industry_news",
        query="",
        workspace=workspace,
        limit=200,
    )

    # 提取所有分类
    categories = set()
    for hit in result["hits"]:
        category = hit.get("category", "未分类")
        if category:
            categories.add(category)

    return ApiResponse(
        success=True,
        data=sorted(list(categories)),
        message="获取成功",
        total=len(categories),
    )
