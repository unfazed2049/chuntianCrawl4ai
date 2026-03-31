"""
竞争对手相关路由
"""

from fastapi import APIRouter, Query
from server.models.search import ApiResponse
from server.models.competitor import CompetitorProfile, CompetitorNews
from server.utils.meilisearch_client import hybrid_search

router = APIRouter()


@router.get("", response_model=ApiResponse[list[CompetitorProfile]])
async def get_competitors(
    workspace: str = Query("default", description="工作空间"),
    limit: int = Query(100, ge=1, le=200, description="返回数量"),
):
    """获取竞争对手列表"""
    result = await hybrid_search(
        index_name="competitor_profiles",
        query="",
        workspace=workspace,
        limit=limit,
    )

    return ApiResponse(
        success=True,
        data=result["hits"],
        message="获取成功",
        total=result["estimatedTotalHits"],
    )


@router.get("/{competitor_id}", response_model=ApiResponse[CompetitorProfile])
async def get_competitor_profile(
    competitor_id: str,
    workspace: str = Query("default", description="工作空间"),
):
    """获取竞争对手档案详情"""
    result = await hybrid_search(
        index_name="competitor_profiles",
        query="",
        workspace=workspace,
        filter_expr=f'competitor_id = "{competitor_id}"',
        limit=1,
    )

    if not result["hits"]:
        return ApiResponse(
            success=False,
            data=None,
            message="未找到该竞争对手",
        )

    return ApiResponse(
        success=True,
        data=result["hits"][0],
        message="获取成功",
    )


@router.get("/{competitor_id}/news", response_model=ApiResponse[list[CompetitorNews]])
async def get_competitor_news(
    competitor_id: str,
    workspace: str = Query("default", description="工作空间"),
    limit: int = Query(50, ge=1, le=100, description="返回数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
):
    """获取竞争对手新闻"""
    result = await hybrid_search(
        index_name="competitor_news",
        query="",
        workspace=workspace,
        filter_expr=f'competitor_id = "{competitor_id}"',
        limit=limit,
        offset=offset,
    )

    return ApiResponse(
        success=True,
        data=result["hits"],
        message="获取成功",
        total=result["estimatedTotalHits"],
    )
